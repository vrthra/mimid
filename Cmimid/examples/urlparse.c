#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <limits.h>

enum url_type {
    URL_NORMAL,
    URL_OLD_TFTP,
    URL_PREFIX
};

struct url_info {
    char *scheme;
    char *user;
    char *passwd;
    char *host;
    unsigned int port;
    char *path;			/* Includes query */
    enum url_type type;
};

void parse_url(struct url_info *ui){
    char url[PATH_MAX];
    fgets(url, MAX, stdin);
    char *p = url;
    char *q, *r, *s;

    memset(ui, 0, sizeof *ui);

    q = strstr(p, "://");
    if (!q) {
        q = strstr(p, "::");
        if (q) {
            *q = '\000';
            ui->scheme = "tftp";
            ui->host = p;
            ui->path = q+2;
            ui->type = URL_OLD_TFTP;
            return;
        } else {
            ui->path = p;
            ui->type = URL_PREFIX;
            return;
        }
    }

    ui->type = URL_NORMAL;

    ui->scheme = p;
    *q = '\000';
    p = q+3;

    q = strchr(p, '/');
    if (q) {
        *q = '\000';
        ui->path = q+1;
        q = strchr(q+1, '#');
    if (q)
        *q = '\000';
    } else {
        ui->path = "";
    }

    r = strchr(p, '@');
    if (r) {
        ui->user = p;
        *r = '\000';
        s = strchr(p, ':');
        if (s) {
            *s = '\000';
            ui->passwd = s+1;
        }
        p = r+1;
    }

    ui->host = p;
    r = strchr(p, ':');
    if (r) {
        *r = '\000';
        ui->port = atoi(r+1);
    }
}

int main(int argc, char* argv[]) {
    struct url_info url;
    parse_url(&url);
    return 0;
}
