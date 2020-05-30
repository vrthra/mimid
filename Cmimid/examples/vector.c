
#include "vector.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Allocate the data structure for the vector
void vector_init(vector* v, size_t data_size) {
	if (v == NULL) return;
	
	v->data = malloc(data_size);
	if (v->data != NULL)
	{
		v->capacity = 1;
        v->data_size = data_size;
        v->size = 0; 
	}
}

// Free the memory of the vector, the pointer to the vector is invalid after this
void vector_free(vector* v)
{
    if (v)
    {
        free(v->data);
		v->data = NULL;
    }
}

// Return the element at index, does not do a range check
void* vector_get(const vector* v, size_t index) {
	return &(v->data[index * v->data_size]);
}

// Return the element at index, return NULL if index is out of range for the vector
void* vector_get_checked(const vector* v, size_t index) {
	return (index < v->size) ? &(v->data[index * v->data_size]) : NULL;
}

// if capacity < new_capacity realloc up to new_capacity
void vector_reserve(vector* v, size_t new_capacity) {
	if (new_capacity <= v->capacity) return;
    void* new_data = realloc(v->data, new_capacity*v->data_size);
    if (new_data) {
        v->capacity = new_capacity;
        v->data = new_data;
    }
    else {
        abort();
    }
}

// Puts an element data[size * data_size], will reserve more space if size == capacity
void vector_push_back(vector* v, void* data) {
    if (v->size >= v->capacity) {
		size_t new_capacity = (v->capacity > 0) ? (size_t)(v->capacity * 2) : 1;
		vector_reserve(v, new_capacity);
    }
    memcpy(vector_get(v,v->size), data, v->data_size);
    ++v->size;
}

void vector_foreach_data(const vector* v, vector_foreach_data_t fp, void* data)
{
	if (v == NULL) return;
	char* item = v->data;
	assert(item != NULL);
	for (size_t i = 0; i < v->size; i++) {
		if (! fp(item, (void *)data)) break;
		item += v->data_size;
	}
}

void vector_foreach(const vector* v, vector_foreach_t fp)
{
	if (v == NULL) return;
	char* item = v->data;
	assert(item != NULL);
	for (size_t i = 0; i < v->size; i++) {
		fp(item);
		item += v->data_size;
	}
}

#ifdef BUILD_TEST

void vector_test_alloc_free(void)
{
	printf("vector_test_alloc_free: ");
	vector v; 
	vector_init(&v, sizeof(int));
    assert(v.capacity == 1);
    assert(v.size == 0);
    assert(v.data_size == sizeof(int));
    assert(v.data != NULL);
	printf("OK\n");
    vector_free(&v);
}

void vector_test_insert_read_int(void)
{
	printf("vector_test_insert_read_int: ");
	int val1 = 0xabcdabcd;
	int val2 = 0xeffeeffe;
	vector v; 
	vector_init(&v, sizeof(int));
	vector_push_back(&v,&val1);
	assert(v.size == 1);
	assert(v.capacity == 1);
	int* p = vector_get(&v, 0);
	assert(*p == val1);
	vector_push_back(&v, &val2);
	p = vector_get(&v, 0);
	assert(*p == val1);
	assert(*(p + 1) == val2);

	printf("OK\n");
	vector_free(&v);
}

void vector_test_insert_read_struct(void)
{
	struct data {
		double d;
		int i;
	};

	printf("vector_test_insert_read_struct: ");
	vector v; 
	vector_init(&v, sizeof(struct data));
	struct data d1 = { 0.05, 123 };
	struct data d2 = { -1.9999e10, -9000 };
	vector_push_back(&v, &d1);
	vector_push_back(&v, &d2);
	struct data* p = vector_get(&v, 0);
	assert((*p).d == d1.d); // Bitcopy should be exactly equal
	assert((*p).i == d1.i);
	p = vector_get(&v, 1);
	assert((*p).i == d2.i);
	assert((*p).d == d2.d);

	printf("OK\n");
	vector_free(&v);
}

void vector_test_safe_get(void)
{
	printf("vector_test_safe_get:  ");
	vector v; 
	vector_init(&v, sizeof(int));
	int val = 0xff;
	vector_push_back(&v, &val);
	vector_push_back(&v, &val);

	assert(NULL == vector_get_checked(&v, -1));
	assert(NULL == vector_get_checked(&v, 2));
	assert(val == *(int*)(vector_get_checked(&v, 1)));

	printf("OK\n");
	vector_free(&v);
}

void vector_test_reserve(void)
{
	printf("vector_test_reserve:  ");
	vector v; 
	vector_init(&v, sizeof(int));
	assert(v.capacity == 1);
	vector_reserve(&v, 10);
	assert(v.capacity == 10);

	// if we didn't assign the correct space VS will shout about overwriting memory in DEBUG
	int* p = (int*)v.data;
	for (int i = 0; i < 10; ++i) {
		*p = i;
		++p;
	}

	printf("OK\n");
	vector_free(&v);
}

void foreach_increment_nodata(void* item)
{
	assert(item != NULL);
	int* val = item;
	*val = *val + 1;
}


void vector_test_foreach_nodata(void)
{
	vector v;
	printf("vector_test_foreach_nodata: ");

	vector_init(&v, sizeof(int));
	int val = 0;

	for (size_t i = 0; i < 5; ++i)
	{
		vector_push_back(&v, &val);
		++val;
	}

	vector_foreach(&v, foreach_increment_nodata);

	for (size_t i = 0; i < 5; ++i)
	{
		int* d = vector_get(&v, i);
		assert(*d == i + 1);
	}

	printf("OK\n");
	vector_free(&v);
}


int foreach_increment_data_null(void* item, void* data)
{
	assert(item != NULL);
	assert(data == NULL);
	int* val = item;
	*val = *val + 1;
	return 1;
}


void vector_test_foreach_data_1(void)
{
	vector v;	
	printf("vector_test_foreach_data_1: ");

	vector_init(&v, sizeof(int));
	int val = 0;

	for (size_t i = 0; i < 5; ++i) {
		vector_push_back(&v, &val);
		++val;
	}

	vector_foreach_data(&v, foreach_increment_data_null, NULL);

	for (size_t i = 0; i < 5; ++i) {
		int* d = vector_get(&v, i);
		assert(*d == i+1);
	}

	printf("OK\n");
	vector_free(&v);
}

struct foreach_data {
	int i;
};

int foreach_increment_data(void* item, void* data)
{
	assert(item != NULL);
	assert(data != NULL);
	int *i = item;
	((struct foreach_data*)data)->i += *i;
	return 1;
}

void vector_test_foreach_data_2(void)
{
	vector v;
	printf("vector_test_foreach_data_2: ");

	vector_init(&v, sizeof(int));
	int val = 4;
	int sum = 0;
	for (size_t i = 0; i < 5; ++i) {
		vector_push_back(&v, &val);
		sum += val;
		++val;
	}

	struct foreach_data data = {.i=0};
	vector_foreach_data(&v, foreach_increment_data, &data);
	assert(data.i == sum);

	printf("OK\n");
	vector_free(&v);
}

void vector_test_all(void)
{
    vector_test_alloc_free();
	vector_test_insert_read_int();
	vector_test_insert_read_struct();
	vector_test_safe_get();
	vector_test_reserve();
	vector_test_foreach_nodata();
	vector_test_foreach_data_1();
	vector_test_foreach_data_2();
}

#endif // UNIT_TEST
