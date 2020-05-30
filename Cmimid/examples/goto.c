#include <stdio.h>
int main(int argc, char** argv) {
  int i = 0;
  while (i < 100) {
    goto x:
    printf("%d\n" , i);
x:  i ++;
  } return 0;
}
