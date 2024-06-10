

ER_ADD_EXECUTABLE(complexbin SOURCES main.cpp)

# checking xpkg-config operation
find_package(PkgConfig REQUIRED)

pkg_check_modules(NCurses REQUIRED ncurses)

target_link_libraries(complexbin complexlib)

# FIXME: this will require devc refatoring that's upcoming
# verifying xpkg-config operation for now...
# target_link_libraries(complexbin ${NCurses_LINK_LIBRARIES})
# target_include_directories(complexbin PRIVATE complexlib ${NCurses_INCLUDE_DIRS})
# target_compile_options(complexbin PRIVATE ${NCurses_CFLAGS_OTHERS})
