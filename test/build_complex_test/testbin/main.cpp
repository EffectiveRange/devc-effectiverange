#include <complexlib/lib.hpp>
// #include <ncurses.h>
#include <iostream>

#include <test.pb.h>

int main(int, char**)
{
    std::cout <<"Meaning of life is " << meaning_of_life() << '\n';
    // initscr();
    // printw( "Meaning of life is %d\n",meaning_of_life());
    // refresh();
    // getch();
    // endwin();
    return 0;
}