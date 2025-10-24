/**
 * HOPPER - Module d'Exécution Système (C)
 * 
 * Ce module gère les actions système directes:
 * - Manipulation de fichiers
 * - Lancement d'applications
 * - Commandes système
 * 
 * Optimisé en C pour des performances maximales
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <microhttpd.h>
#include <cjson/cJSON.h>
#include <time.h>

#define PORT 5002
#define MAX_COMMAND_LENGTH 1024
#define MAX_PATH_LENGTH 512

// Structure pour les réponses
typedef struct {
    int success;
    char message[1024];
    char data[2048];
} ExecutionResult;

// Prototypes
static enum MHD_Result handle_request(void *cls, struct MHD_Connection *connection,
                                     const char *url, const char *method,
                                     const char *version, const char *upload_data,
                                     size_t *upload_data_size, void **con_cls);
ExecutionResult execute_command(const char *command);
ExecutionResult create_file(const char *path);
ExecutionResult delete_file(const char *path);
ExecutionResult list_directory(const char *path);
ExecutionResult open_application(const char *app_name);
char* create_json_response(ExecutionResult result);
void log_message(const char *level, const char *message);

/**
 * Point d'entrée principal
 */
int main() {
    struct MHD_Daemon *daemon;
    
    log_message("INFO", "🚀 Démarrage du module d'exécution système");
    log_message("INFO", "Port: 5002");
    
    daemon = MHD_start_daemon(MHD_USE_SELECT_INTERNALLY, PORT, NULL, NULL,
                             &handle_request, NULL, MHD_OPTION_END);
    
    if (daemon == NULL) {
        log_message("ERROR", "Impossible de démarrer le serveur HTTP");
        return 1;
    }
    
    log_message("INFO", "✅ Module d'exécution système prêt");
    
    // Boucle infinie - le serveur tourne en fond
    while (1) {
        sleep(1);
    }
    
    MHD_stop_daemon(daemon);
    return 0;
}

/**
 * Gestionnaire des requêtes HTTP
 */
static enum MHD_Result handle_request(void *cls, struct MHD_Connection *connection,
                                     const char *url, const char *method,
                                     const char *version, const char *upload_data,
                                     size_t *upload_data_size, void **con_cls) {
    struct MHD_Response *response;
    enum MHD_Result ret;
    char response_text[4096];
    ExecutionResult result;
    
    // Route: /health
    if (strcmp(url, "/health") == 0 && strcmp(method, "GET") == 0) {
        snprintf(response_text, sizeof(response_text),
                "{\"status\": \"healthy\", \"service\": \"system_executor\"}");
        
        response = MHD_create_response_from_buffer(strlen(response_text),
                                                   (void *)response_text,
                                                   MHD_RESPMEM_MUST_COPY);
        MHD_add_response_header(response, "Content-Type", "application/json");
        ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
        MHD_destroy_response(response);
        return ret;
    }
    
    // Route: /execute (POST)
    if (strcmp(url, "/execute") == 0 && strcmp(method, "POST") == 0) {
        // Pour simplification, on accepte une commande basique
        // Dans la vraie implémentation, parser le JSON du POST
        
        log_message("INFO", "📥 Requête d'exécution reçue");
        
        // Exemple simple: créer un fichier test
        result = create_file("/tmp/hopper_test.txt");
        
        char *json_response = create_json_response(result);
        response = MHD_create_response_from_buffer(strlen(json_response),
                                                   (void *)json_response,
                                                   MHD_RESPMEM_MUST_COPY);
        MHD_add_response_header(response, "Content-Type", "application/json");
        ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
        MHD_destroy_response(response);
        free(json_response);
        
        return ret;
    }
    
    // Route non trouvée
    const char *not_found = "{\"error\": \"Route not found\"}";
    response = MHD_create_response_from_buffer(strlen(not_found),
                                               (void *)not_found,
                                               MHD_RESPMEM_PERSISTENT);
    MHD_add_response_header(response, "Content-Type", "application/json");
    ret = MHD_queue_response(connection, MHD_HTTP_NOT_FOUND, response);
    MHD_destroy_response(response);
    
    return ret;
}

/**
 * Crée un fichier
 */
ExecutionResult create_file(const char *path) {
    ExecutionResult result;
    FILE *file;
    
    log_message("INFO", "Création de fichier");
    
    file = fopen(path, "w");
    if (file == NULL) {
        result.success = 0;
        snprintf(result.message, sizeof(result.message),
                "Erreur: impossible de créer le fichier %s", path);
        result.data[0] = '\0';
        log_message("ERROR", result.message);
        return result;
    }
    
    fprintf(file, "Fichier créé par HOPPER - %ld\n", time(NULL));
    fclose(file);
    
    result.success = 1;
    snprintf(result.message, sizeof(result.message),
            "Fichier créé avec succès: %s", path);
    snprintf(result.data, sizeof(result.data),
            "{\"path\": \"%s\"}", path);
    
    log_message("SUCCESS", result.message);
    return result;
}

/**
 * Supprime un fichier
 */
ExecutionResult delete_file(const char *path) {
    ExecutionResult result;
    
    log_message("INFO", "Suppression de fichier");
    
    if (unlink(path) == 0) {
        result.success = 1;
        snprintf(result.message, sizeof(result.message),
                "Fichier supprimé: %s", path);
        result.data[0] = '\0';
        log_message("SUCCESS", result.message);
    } else {
        result.success = 0;
        snprintf(result.message, sizeof(result.message),
                "Erreur: impossible de supprimer %s", path);
        result.data[0] = '\0';
        log_message("ERROR", result.message);
    }
    
    return result;
}

/**
 * Liste un répertoire
 */
ExecutionResult list_directory(const char *path) {
    ExecutionResult result;
    char command[MAX_COMMAND_LENGTH];
    FILE *fp;
    char buffer[1024];
    
    log_message("INFO", "Liste du répertoire");
    
    // Utilisation de la commande ls (macOS/Linux)
    snprintf(command, sizeof(command), "ls -la %s 2>&1", path);
    
    fp = popen(command, "r");
    if (fp == NULL) {
        result.success = 0;
        snprintf(result.message, sizeof(result.message),
                "Erreur: impossible de lister %s", path);
        result.data[0] = '\0';
        return result;
    }
    
    result.data[0] = '\0';
    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        strncat(result.data, buffer, sizeof(result.data) - strlen(result.data) - 1);
    }
    
    pclose(fp);
    
    result.success = 1;
    snprintf(result.message, sizeof(result.message),
            "Contenu de %s listé", path);
    
    log_message("SUCCESS", result.message);
    return result;
}

/**
 * Ouvre une application
 */
ExecutionResult open_application(const char *app_name) {
    ExecutionResult result;
    char command[MAX_COMMAND_LENGTH];
    
    log_message("INFO", "Ouverture d'application");
    
    // Sur macOS, utiliser la commande 'open'
    snprintf(command, sizeof(command), "open -a \"%s\" 2>&1", app_name);
    
    int ret = system(command);
    
    if (ret == 0) {
        result.success = 1;
        snprintf(result.message, sizeof(result.message),
                "Application lancée: %s", app_name);
        snprintf(result.data, sizeof(result.data),
                "{\"app\": \"%s\"}", app_name);
        log_message("SUCCESS", result.message);
    } else {
        result.success = 0;
        snprintf(result.message, sizeof(result.message),
                "Erreur: impossible de lancer %s", app_name);
        result.data[0] = '\0';
        log_message("ERROR", result.message);
    }
    
    return result;
}

/**
 * Crée une réponse JSON
 */
char* create_json_response(ExecutionResult result) {
    cJSON *root = cJSON_CreateObject();
    
    cJSON_AddBoolToObject(root, "success", result.success);
    cJSON_AddStringToObject(root, "message", result.message);
    
    if (strlen(result.data) > 0) {
        cJSON *data = cJSON_Parse(result.data);
        if (data != NULL) {
            cJSON_AddItemToObject(root, "data", data);
        }
    }
    
    char *json_string = cJSON_Print(root);
    cJSON_Delete(root);
    
    return json_string;
}

/**
 * Enregistre un message de log
 */
void log_message(const char *level, const char *message) {
    time_t now = time(NULL);
    char timestamp[26];
    struct tm *tm_info = localtime(&now);
    
    strftime(timestamp, 26, "%Y-%m-%d %H:%M:%S", tm_info);
    
    printf("[%s] [%s] %s\n", timestamp, level, message);
    fflush(stdout);
}
