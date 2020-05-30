#ifndef HS_VECTOR_H
#define HS_VECTOR_H

#include <stddef.h>

typedef struct {
    size_t capacity;
    size_t data_size;
    size_t size;
    char* data;
} vector;

void vector_init(vector* v, size_t data_size);

void vector_free(vector* v);

void* vector_get(const vector* v, size_t index);

void* vector_get_checked(const vector* v, size_t index);

void vector_reserve(vector* v, size_t new_capacity);

void vector_push_back(vector* v, void* data);


typedef void(*vector_foreach_t)(void*);

void vector_foreach(const vector* v, vector_foreach_t fp);

typedef int(*vector_foreach_data_t)(void*, void*);

void vector_foreach_data(const vector* v, vector_foreach_data_t fp, void* data);

#ifdef BUILD_TEST
void vector_test_all();
#endif

#endif
