# [VEGA-PATCH 7 T08:40] Stub amd_comgr per Windows ROCm
set(amd_comgr_FOUND TRUE)
set(amd_comgr_VERSION "2.7.0")
set(amd_comgr_LIBRARIES "amd_comgr")
if(NOT TARGET amd_comgr)
  add_library(amd_comgr INTERFACE IMPORTED)
endif()
