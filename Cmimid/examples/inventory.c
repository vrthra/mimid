#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int max_size = 1024;

char* process_van(char* year, char* company, char* model, char* my_string) {
    char *current = my_string;
    char* fmt = "We have a %s %s van from %s vintage.\n";
    int written = snprintf(current, max_size, fmt, company, model, year);

    current += written;
    int rem = (max_size - written);

    if(atoi(year) > 2010) {
        snprintf(current, rem, "It is a recent model!\n");
    } else {
        snprintf(current, rem, "It is an old but reliable model!\n");
    }
    return my_string;
}

char* process_car(char* year, char* company, char* model, char* my_string) {
    char *current = my_string;
    char* fmt = "We have a %s %s car from %s vintage.\n";
    int written = snprintf(current, max_size, fmt, company, model, year);
    int rem = (max_size - written);

    if(atoi(year) > 2010) {
        snprintf(current, rem, "It is a recent model!\n");
    } else {
        snprintf(current, rem, "It is an old but reliable model!\n");
    }
    return my_string;
}

char* process_vehicle(char* vehicle_str, char* my_string) {
    char *data[4];
    int index = 0;
    char* str = vehicle_str;

    for(;;) {
       data[index] = strtok(str, ",");
       if (!data[index]) break;

       str = NULL;
       index += 1;
    }

    char* year = data[0];
    char* kind = data[1];
    char* company = data[2];
    char* model = data[3];

    if(!strcmp(kind, "van")) {
        return process_van(year, company, model, my_string);
    } else if (!strcmp(kind, "car")) {
        return process_car(year, company, model, my_string);
    } else {
        fprintf(stderr, "Invalid entry");
        return NULL;
    }
}

int main(int argc, char* argv[]) {
    /* format: year, kind, company, model */
    char *my_string = malloc(sizeof(char) * max_size);
    char* result = process_vehicle(argv[1], my_string);
    printf("%s", result);
    
    free(my_string);
    return 0;
}
