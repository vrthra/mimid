#ifndef CALC_PARSE_H
#define CALC_PARSE_H

struct index_num {
    int index;
    char *number_str;
};

struct index_expr {
    int index;
    char** expr_list;
};

struct index_num parse_num(char* s, int i);
struct index_expr parse_paren(char* s, int i);
struct index_expr parse_expr(char* s, int i, int seen_paren);
#define BUFFER 10240

#endif //CALC_PARSE_H
