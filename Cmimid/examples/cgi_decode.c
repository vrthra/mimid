#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int hex_values[256];

void init_hex_values() {
  for (int i = 0; i < sizeof(hex_values) / sizeof(int); i++) {
    hex_values[i] = -1;
  }
  hex_values['0'] = 0;
  hex_values['1'] = 1;
  hex_values['2'] = 2;
  hex_values['3'] = 3;
  hex_values['4'] = 4;
  hex_values['5'] = 5;
  hex_values['6'] = 6;
  hex_values['7'] = 7;
  hex_values['8'] = 8;
  hex_values['9'] = 9;

  hex_values['a'] = 10;
  hex_values['b'] = 11;
  hex_values['c'] = 12;
  hex_values['d'] = 13;
  hex_values['e'] = 14;
  hex_values['f'] = 15;

  hex_values['A'] = 10;
  hex_values['B'] = 11;
  hex_values['C'] = 12;
  hex_values['D'] = 13;
  hex_values['E'] = 14;
  hex_values['F'] = 15;
}

int cgi_decode(char *s, char *t) {
  while (*s != '\0') {
    if (*s == '+') {
      *t++ = ' ';
    } else if (*s == '%') {
      int digit_high = *++s;
      int digit_low = *++s;
      if (hex_values[digit_high] >= 0 && hex_values[digit_low] >= 0) {
        *t++ = hex_values[digit_high] * 16 + hex_values[digit_low];
      } else {
        return -1;
      }
    } else {
      *t++ = *s;
    }
    s++;
  }
  *t = '\0';
  return 0;
}

void strip_input(char *my_string) {
  int read = strlen(my_string);
  if (my_string[read - 1] == '\n') {
    my_string[read - 1] = '\0';
  }
}

int main(int argc, char *argv[]) {
  char my_string[10240];
  char result[10240];
  init_hex_values();
  int ret = -1;
  if (argc == 1) {
    char *v = fgets(my_string, 10240, stdin);
    if (!v) {
      exit(1);
    }
    strip_input(my_string);
  } else {
    strcpy(my_string, argv[1]);
    strip_input(my_string);
  }
  printf("val: <%s>\n", my_string);
  ret = cgi_decode(my_string, &result);
  return ret;
}
