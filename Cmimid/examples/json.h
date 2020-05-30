#ifndef HS_JSON_H
#define HS_JSON_H

#define BUFFER 10240

#include "vector.h"
/*
enum json_value_type {
	TYPE_NULL,
	TYPE_BOOL,
	TYPE_NUMBER,
	TYPE_OBJECT, // Is a vector with pairwise entries, key, value
	TYPE_ARRAY, // Is a vector, all entries are plain 
	TYPE_STRING,
	TYPE_KEY
};*/

typedef struct {
	int type;
	union {
		int boolean;
		double number;
		char* string;
		char* key;
		vector array;
		vector object;
	} value;
} json_value;

// Parse string into structure of json elements and values
// return 1 if successful.
int json_parse(const char* input, json_value* root);

// Free the structure and all the allocated values
void json_free_value(json_value* val);

// Convert value to string if possible, asserts if not
char* json_value_to_string(json_value* value);

// Convert value to double if possible asserts if not
double json_value_to_double(json_value* value);

// Convert value to bool if possible asserts if not
int json_value_to_bool(json_value* value);

// Convert value to vector if it's an array asserts if not
vector* json_value_to_array(json_value* value);

// Convert value to vector if it's an object, asserts if not
vector* json_value_to_object(json_value* value);

// Fetch the value with given index from root, asserts if root is not array
json_value* json_value_at(const json_value* root, size_t index);

// Fetche the value with the given key from root, asserts if root is not object
json_value * json_value_with_key(const json_value * root, const char * key);

#endif
