
int main(int argc, char** argv) {
    int i = 0, j = 1;
    while (i < 5) {
        i += 1;
        j = 26;
        continue;
    }
}


int while_break() {
    int i = 0, j = 1;
    while (i < 5) {
        i += 1;
        j = 26;
        if (i == 0) {
          break;
        }
    }
}

int while_continue() {
    int i = 0, j = 1;
    while (i < 5) {
        i += 1;
        j = 26;
        if (i == 0) {
          continue;
        }
    }
}


void test() {
    int i = 0, j = 1;
    while (i < 5) {
        i += 1;
        while(j < 3)
          j = 26;
    }

    while(j > 10) {
          j = 26;
    }
}
