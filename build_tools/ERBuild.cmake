
if(COMMAND cmake_policy) 
  cmake_policy(SET CMP0003 NEW)
  cmake_policy(SET CMP0048 NEW)
endif()

enable_language(C CXX)

include(GNUInstallDirs)

function(ER_DEPS)
  find_program(ER_DPKGDEPS dpkgdeps HINTS ${CMAKE_CURRENT_FUNCTION_LIST_DIR} )

  if(NOT ER_DPKGDEPS)
  message(FATAL_ERROR ":dpkgdeps tool not found!")
  endif()

  if (NOT DEFINED ${PROJECT_NAME}_DEPS_INSTALLED )
    message(STATUS  ":Installing dependencies for ${PROJECT_NAME}")

    if (DEFINED CMAKE_STAGING_PREFIX AND NOT CMAKE_STAGING_PREFIX STREQUAL "")
    set(DEPS_STAGING_ARG "--staging=${CMAKE_STAGING_PREFIX}")
    endif()

    if (DEFINED CMAKE_SYSROOT AND NOT CMAKE_SYSROOT STREQUAL "")
    set(DEPS_SYSROOT_ARG "--sysroot=${CMAKE_SYSROOT}")
    endif()
    
    if (NOT DEFINED CMAKE_SYSROOT OR  CPACK_DEBIAN_PACKAGE_ARCHITECTURE STREQUAL "")
    EXECUTE_PROCESS( COMMAND dpkg --print-architecture  COMMAND tr -d '\n' OUTPUT_VARIABLE CPACK_DEBIAN_PACKAGE_ARCHITECTURE  )
    endif()

    execute_process(COMMAND ${ER_DPKGDEPS} -v --build ${CMAKE_CURRENT_BINARY_DIR} --arch ${CPACK_DEBIAN_PACKAGE_ARCHITECTURE} ${DEPS_STAGING_ARG} ${DEPS_SYSROOT_ARG} -- ${CMAKE_CURRENT_LIST_DIR} 
    COMMAND_ERROR_IS_FATAL ANY)

    execute_process(COMMAND ${ER_DPKGDEPS} --arch ${CPACK_DEBIAN_PACKAGE_ARCHITECTURE} --debdeps "${CMAKE_CURRENT_LIST_DIR}"  OUTPUT_VARIABLE _ER_DEBDEPS  COMMAND_ERROR_IS_FATAL ANY)

    string(STRIP "${_ER_DEBDEPS}" _ER_DEBDEPS)

    message(INFO ":Project debian deps: ${_ER_DEBDEPS}" )

    set(${PROJECT_NAME}_DEBDEPS "${_ER_DEBDEPS}" CACHE STRING "${PROJECT_NAME} debian package dependencies for installation" )

    set(${PROJECT_NAME}_DEPS_INSTALLED ON CACHE BOOL "${PROJECT_NAME} deps installed" )
  endif()
endfunction()

function(_ER_ADD_BINARY_IMPL name)

  cmake_parse_arguments(_ERB "EXE;STATICLIB;LIB" "" "SOURCES" ${ARGN})

  if (_ERB_UNPARSED_ARGUMENTS)
    message(FATAL_ERROR ":ER_ADD_EXECUTABLE: ${_ERB_UNPARSED_ARGUMENTS}: unexpected arguments")
  endif()

  if(_ERB_EXE)
    add_executable(${name} ${_ERB_SOURCES})
  elseif(_ERB_STATICLIB)
    add_library(${name} STATIC ${_ERB_SOURCES})
  elseif(_ERB_LIB)
    add_library(${name} SHARED ${_ERB_SOURCES})
  else()
    message(FATAL_ERROR ":Unknown target type to add")
  endif()


  install(TARGETS ${name} RUNTIME DESTINATION bin LIBRARY DESTINATION lib INCLUDES DESTINATION include PUBLIC_HEADER DESTINATION include)

  if(NOT _ERB_EXE)
    # installing public headers directory verbatim for libraries
    if(IS_DIRECTORY "${CMAKE_CURRENT_LIST_DIR}/include/")
      install(DIRECTORY "${CMAKE_CURRENT_LIST_DIR}/include/" # source directory
              DESTINATION "include/" # target directory
      )
    endif()
  endif()


endfunction()

function(ER_ADD_EXECUTABLE name)
_ER_ADD_BINARY_IMPL(${name} EXE ${ARGN})
endfunction()

function(ER_ADD_SHARED_LIBRARY name)
_ER_ADD_BINARY_IMPL(${name} LIB ${ARGN})
endfunction()

function(ER_ADD_STATIC_LIBRARY name)
_ER_ADD_BINARY_IMPL(${name} STATICLIB ${ARGN})
endfunction()

macro(ER_ENABLE_TEST)
  if(${CMAKE_HOST_SYSTEM_PROCESSOR} STREQUAL ${CMAKE_SYSTEM_PROCESSOR})
    message(INFO ":Enabling testing as ${CMAKE_HOST_SYSTEM_PROCESSOR} (host) == ${CMAKE_SYSTEM_PROCESSOR} (target)")
    enable_testing()
  else()
    message(INFO ":Disabling testing as ${CMAKE_HOST_SYSTEM_PROCESSOR} (host) != ${CMAKE_SYSTEM_PROCESSOR} (target)")
  endif()
endmacro()

macro(ER_PACK)

  set(CPACK_PACKAGE_NAME ${PROJECT_NAME}
      CACHE STRING "The resulting package name"
  )
  set(CPACK_PACKAGE_INSTALL_DIRECTORY ${CPACK_PACKAGE_NAME})

  set(CPACK_PACKAGING_INSTALL_PREFIX "/usr/local")

  set(CPACK_PACKAGE_VERSION_MAJOR ${PROJECT_VERSION_MAJOR})
  set(CPACK_PACKAGE_VERSION_MINOR ${PROJECT_VERSION_MINOR})
  set(CPACK_PACKAGE_VERSION_PATCH ${PROJECT_VERSION_PATCH})

  set(CPACK_VERBATIM_VARIABLES YES)

  set(CPACK_GENERATOR "DEB")
  set(CPACK_DEBIAN_FILE_NAME DEB-DEFAULT)
  set(CPACK_DEBIAN_PACKAGE_VERSION ${PROJECT_VERSION})
  set(CPACK_DEBIAN_PACKAGE_RELEASE 1)
  set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Installable package of ${PROJECT_NAME} project")

  message(INFO ":Setup packing for project ${PROJECT_NAME}")
  if ( PROJECT_DESCRIPTION STREQUAL "" )
  message( FATAL_ERROR ":Project description missing for project ${PROJECT_NAME}, CMake will exit." )
  endif()

  set(CPACK_PACKAGE_DESCRIPTION ${PROJECT_DESCRIPTION})
  
  set(CPACK_PACKAGE_DIRECTORY "/opt/debs")

  set(CPACK_DEBIAN_PACKAGE_MAINTAINER "Effective Range Kft. <info@effective-range.com>")
  set(CPACK_DEBIAN_PACKAGE_HOMEPAGE "https://www.effective-range.com/")

  set(CPACK_DEBIAN_PACKAGE_DEPENDS "${${PROJECT_NAME}_DEBDEPS}" )


  include(CPack)

endmacro(ER_PACK)