


# example for generating source files (with hostinstall feature)
find_package(Protobuf REQUIRED)


# By default generates to ${CMAKE_CURRENT_BINARY_DIR}
protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS test.proto PROTOC_OUT_DIR)

ER_ADD_EXECUTABLE(complexbin SOURCES main.cpp ${PROTO_SRCS} ${PROTO_HDRS})
# ${CMAKE_CURRENT_BINARY_DIR} is added as an include directory to be able to pull in generated source files
target_include_directories(complexbin PRIVATE ${Protobuf_INCLUDE_DIRS} ${CMAKE_CURRENT_BINARY_DIR})

# checking xpkg-config operation
find_package(PkgConfig REQUIRED)

pkg_check_modules(NCurses REQUIRED ncurses)

target_link_libraries(complexbin complexlib ${Protobuf_LIBRARIES})

# FIXME: this will require devc refatoring that's upcoming
# verifying xpkg-config operation for now...
# target_link_libraries(complexbin ${NCurses_LINK_LIBRARIES})
# target_include_directories(complexbin PRIVATE complexlib ${NCurses_INCLUDE_DIRS})
# target_compile_options(complexbin PRIVATE ${NCurses_CFLAGS_OTHERS})
