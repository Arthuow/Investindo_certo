#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>
#include <cjson/cJSON.h>
#include <sqlite3.h>
#include <time.h>

#define URL_SIZE 256

// Função de callback para capturar resposta HTTP
struct MemoryStruct {
    char *memory;
    size_t size;
};

static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    struct MemoryStruct *mem = (struct MemoryStruct *)userp;

    char *ptr = realloc(mem->memory, mem->size + realsize + 1);
    if (ptr == NULL) {
        // Falha ao alocar memória
        return 0;
    }

    mem->memory = ptr;
    memcpy(&(mem->memory[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->memory[mem->size] = 0;

    return realsize;
}

// Função para obter dados do Yahoo Finance
char* obter_dados_ativo(const char *ativo) {
    CURL *curl;
    CURLcode res;
    struct MemoryStruct chunk;

    chunk.memory = malloc(1);  // Iniciar com espaço para string vazia
    chunk.size = 0;            // Sem dados ainda

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if (curl) {
        char url[URL_SIZE];
        snprintf(url, URL_SIZE, "https://query1.finance.yahoo.com/v7/finance/quote?symbols=%s", ativo);

        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);

        // Perform the request
        res = curl_easy_perform(curl);

        if (res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        }

        // Cleanup
        curl_easy_cleanup(curl);
    }

    curl_global_cleanup();

    return chunk.memory;
}

// Função para inserir dados no banco de dados SQLite
void inserir_preco_no_banco(sqlite3 *db, const char *ativo, double preco, const char *data_atualizacao) {
    char *errmsg = 0;
    char sql[256];
    snprintf(sql, sizeof(sql),
             "INSERT OR REPLACE INTO preco_atual_intraday (ativo, preco_atual, data_atualizacao) "
             "VALUES ('%s', %f, '%s');", ativo, preco, data_atualizacao);

    if (sqlite3_exec(db, sql, 0, 0, &errmsg) != SQLITE_OK) {
        fprintf(stderr, "Erro ao inserir no banco de dados: %s\n", errmsg);
        sqlite3_free(errmsg);
    }
}

int main() {
    // Exemplo: Conectar ao banco de dados SQLite
    sqlite3 *db;
    if (sqlite3_open("carteira.db", &db)) {
        fprintf(stderr, "Não foi possível abrir o banco de dados: %s\n", sqlite3_errmsg(db));
        return 1;
    }

    // Exemplo de ativo
    const char *ativo = "ABEV3.SA";

    // Obter dados do ativo
    char *dados_json = obter_dados_ativo(ativo);

    // Processar o JSON (usando cJSON)
    cJSON *json = cJSON_Parse(dados_json);
    if (json == NULL) {
        fprintf(stderr, "Erro ao analisar JSON\n");
    } else {
        cJSON *quoteResponse = cJSON_GetObjectItemCaseSensitive(json, "quoteResponse");
        cJSON *result = cJSON_GetObjectItemCaseSensitive(quoteResponse, "result");

        if (cJSON_IsArray(result)) {
            cJSON *quote = cJSON_GetArrayItem(result, 0);
            double preco_atual = cJSON_GetObjectItemCaseSensitive(quote, "regularMarketPrice")->valuedouble;
            const char *data_atualizacao = cJSON_GetObjectItemCaseSensitive(quote, "regularMarketTime")->valuestring;

            // Inserir os dados no banco de dados
            inserir_preco_no_banco(db, ativo, preco_atual, data_atualizacao);
        }
    }

    // Limpeza
    cJSON_Delete(json);
    free(dados_json);
    sqlite3_close(db);

    return 0;
}
