# [VEGA-PATCH 6 T08:35 18 giu] Stub Findhsa-runtime64.cmake per Windows
# hsa-runtime64Config.cmake non distribuito su Windows AMD ROCm install.
# Su Windows HSA runtime è implementato via amdhip64.dll System32, non separato.
# Stubbed per consentire find_package(hsa-runtime64) successo + fake target.

set(hsa-runtime64_FOUND TRUE)
set(hsa-runtime64_VERSION "1.13.0")
set(hsa-runtime64_LIBRARIES "amdhip64")
set(hsa-runtime64_INCLUDE_DIRS "")

if(NOT TARGET hsa-runtime64::hsa-runtime64)
  add_library(hsa-runtime64::hsa-runtime64 INTERFACE IMPORTED)
  set_target_properties(hsa-runtime64::hsa-runtime64 PROPERTIES
    INTERFACE_LINK_LIBRARIES "amdhip64")
endif()
