int main(int argc, char** argv) {
    int i = 5;
    switch (i)
    {
        case 0:
            i = 10;
            i += 1;
            break;
        case 3:
            break;
        case 4:
        case 1:
            i = 20;
            break;
        default:
            i = 0;
    }
    switch (i > 1) {
      default:
            i = 0;
            i = 1;
        /*break; Not allowed in default*/
    }
    return 0;
}

