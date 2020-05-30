#include "json.h"
/* From
 * https://raw.githubusercontent.com/HarryDC/JsonParser/53197e0b84a7c8d3d57b840e40ea13efdd01d57d/src/json.c*/
/*I have no idea why CLANG has a problem with enumed case labels
TYPE_NULL = 0;
TYPE_BOOL = 1;
TYPE_NUMBER = 2;
TYPE_OBJECT = 3;
TYPE_ARRAY = 4;
TYPE_STRING = 5;
TYPE_KEY = 6;*/

#include <assert.h>
#include <ctype.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>

static int json_parse_value(const char **cursor, json_value *parent);

int isspace_(char c) {
  return isspace(c);
}

int iscntrl_(char c) {
  return iscntrl(c);
}

static void skip_whitespace(const char **cursor) {
  if (**cursor == '\0')
    return;
  while (iscntrl_(**cursor) || isspace_(**cursor))
    ++(*cursor);
}

static int has_char(const char **cursor, char character) {
  skip_whitespace(cursor);
  int success = **cursor == character;
  if (success)
    ++(*cursor);
  return success;
}

static int json_parse_object(const char **cursor, json_value *parent) {
  json_value result;
  result.type = 3; /*TYPE_OBJECT*/;
  /*vector_init(&result.value.object, sizeof(json_value));*/

  int success = 1;
  while (success && !has_char(cursor, '}')) {
    json_value key;
    key.type = 0; /*TYPE_NULL*/
    json_value value;
    value.type = 0; /*TYPE_NULL*/
    success = json_parse_value(cursor, &key);
    success = success && has_char(cursor, ':');
    success = success && json_parse_value(cursor, &value);

    if (success) {
      /*vector_push_back(&result.value.object, &key);
      vector_push_back(&result.value.object, &value);*/
    } else {
      json_free_value(&key);
      break;
    }
    skip_whitespace(cursor);
    if (has_char(cursor, '}'))
      break;
    else if (has_char(cursor, ','))
      continue;
    else
      success = 0;
  }

  if (success) {
    *parent = result;
  } else {
    json_free_value(&result);
  }

  return success;
}

static int json_parse_array(const char **cursor, json_value *parent) {
  int success = 1;
  if (**cursor == ']') {
    ++(*cursor);
    return success;
  }
  while (success) {
    json_value new_value;
    new_value.type = 0; /*TYPE_NULL*/
    success = json_parse_value(cursor, &new_value);
    if (!success)
      break;
    skip_whitespace(cursor);
    /*vector_push_back(&parent->value.array, &new_value);*/
    skip_whitespace(cursor);
    if (has_char(cursor, ']'))
      break;
    else if (has_char(cursor, ','))
      continue;
    else
      success = 0;
  }
  return success;
}

void json_free_value(json_value *val) {
  if (!val)
    return;

  switch (val->type) {
  case 5 /*TYPE_STRING*/: {
    free(val->value.string);
    val->value.string = 0;
    break;
  }
  case 4 /*TYPE_ARRAY*/: {
    /*vector_foreach(&(val->value.array), (void (*)(void *))json_free_value);
    vector_free(&(val->value.array));*/
    break;
  }
  case 3 /*TYPE_OBJECT*/: {
    /*vector_foreach(&(val->value.array), (void (*)(void *))json_free_value);
    vector_free(&(val->value.array));*/
    break;
  }
  }

  val->type = 0 /*TYPE_NULL*/;
}

int json_is_literal(const char **cursor, const char *literal) {
  size_t cnt = strlen(literal);
  if (strncmp(*cursor, literal, cnt) == 0) {
    *cursor += cnt;
    return 1;
  }
  return 0;
}

static int json_parse_value(const char **cursor, json_value *parent) {
  /* Eat whitespace */
  int success = 0;
  skip_whitespace(cursor);
  switch (**cursor) {
  case '\0': {
    /* If parse_value is called with the cursor at the end of the string that's a failure*/
    success = 0;
    break;
  }
  case '"': {
    ++*cursor;
    const char *start = *cursor;
    char *end = (char*) strchr(*cursor, '"');
    if (end) {
      size_t len = end - start;
      char *new_string = (char*) malloc((len + 1) * sizeof(char));
      memcpy(new_string, start, len);
      new_string[len] = '\0';

      if (len != strlen(new_string)) {
        exit(100);
      }

      parent->type = 5 /*TYPE_STRING*/;
      parent->value.string = new_string;

      *cursor = end + 1;
      success = 1;
    }
    break;
  }
  case '{': {
    ++(*cursor);
    skip_whitespace(cursor);
    success = json_parse_object(cursor, parent);
    break;
  }
  case '[': {
    parent->type = 4 /*TYPE_ARRAY*/;
    /*vector_init(&parent->value.array, sizeof(json_value));*/
    ++(*cursor);
    skip_whitespace(cursor);
    success = json_parse_array(cursor, parent);
    if (!success) {
      /*vector_free(&parent->value.array);*/
    }
    break;
  }
  case 't': {
    success = json_is_literal(cursor, "true");
    if (success) {
      parent->type = 1; /* TYPE_BOOL;*/
      parent->value.boolean = 1;
    }
    break;
  }
  case 'f': {
    success = json_is_literal(cursor, "false");
    if (success) {
      parent->type = 1; /* TYPE_BOOL;*/
      parent->value.boolean = 0;
    }
    break;
  }
  case 'n': {
    success = json_is_literal(cursor, "null");
    break;
  }
  default: {
    char *end;
    double number = strtod(*cursor, &end);
    if (*cursor != end) {
      parent->type = 2 /*TYPE_NUMBER*/;
      parent->value.number = number;
      *cursor = end;
      success = 1;
    }
  }
  }

  return success;
}

int json_parse(const char *input, json_value *result) {
  const char** cursor = &input;
  int val = json_parse_value(cursor, result);
  while (isspace_(**cursor)) ++(*cursor);
  if (strlen(*cursor) != 0){
    return 0;
  }
  return val;
}

/*void strip_input(char* my_string) {
    int read = strlen(my_string);
    if (my_string[read-1] ==  '\n'){
        my_string[read-1] = '\0';
    }
}*/

int main(int argc, char *argv[]) {
  char my_string[10240];
  json_value result;
  result.type = 0;/*TYPE_NULL*/
  int ret = -1;
  if (argc == 1) {
    int chars = read(fileno(stdin), my_string, 10240);
    if (!chars) {
      exit(1);
    }
    my_string[chars] = 0;
    /*char *v = fgets(my_string, 10240, stdin);
    if (!v) {
      exit(1);
    }*/
    /*strip_input(my_string);*/
  } else {
    int fd = open(argv[1], O_RDONLY);
    int chars = read(fd, my_string, 10240);
    if (!chars) {
      exit(3);
    }
    my_string[chars] = 0;
    /*chars = strip_input(my_string);
    if (!chars) {
      exit(4);
    }*/
    close(fd);
  }
  printf("val: <%s>\n", my_string);
  ret = json_parse(my_string, &result);
  json_free_value(&result);
  if (ret == 1) {
    return 0;
  } else {
    return 1;
  }
}
