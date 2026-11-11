set(PYTORCH_FOUND_HIP FALSE)

if(NOT DEFINED ENV{ROCM_PATH})
  set(ROCM_PATH /opt/rocm)
else()
  set(ROCM_PATH $ENV{ROCM_PATH})
endif()
if(NOT DEFINED ENV{ROCM_INCLUDE_DIRS})
  set(ROCM_INCLUDE_DIRS ${ROCM_PATH}/include)
else()
  set(ROCM_INCLUDE_DIRS $ENV{ROCM_INCLUDE_DIRS})
endif()

if(NOT EXISTS ${ROCM_PATH})
  return()
endif()

# MAGMA_HOME
if(NOT DEFINED ENV{MAGMA_HOME})
  set(MAGMA_HOME ${ROCM_PATH}/magma)
  set(ENV{MAGMA_HOME} ${ROCM_PATH}/magma)
else()
  set(MAGMA_HOME $ENV{MAGMA_HOME})
endif()

torch_hip_get_arch_list(PYTORCH_ROCM_ARCH)
if(PYTORCH_ROCM_ARCH STREQUAL "")
  message(FATAL_ERROR "No GPU arch specified for ROCm build. Please use PYTORCH_ROCM_ARCH environment variable to specify GPU archs to build for.")
endif()
message("Building PyTorch for GPU arch: ${PYTORCH_ROCM_ARCH}")

# Add HIP to the CMAKE Module Path
set(CMAKE_MODULE_PATH ${ROCM_PATH}/lib/cmake/hip ${CMAKE_MODULE_PATH})

macro(find_package_and_print_version PACKAGE_NAME)
  find_package("${PACKAGE_NAME}" ${ARGN})
  message("${PACKAGE_NAME} VERSION: ${${PACKAGE_NAME}_VERSION}")
endmacro()

# Find the HIP Package
find_package_and_print_version(HIP 1.0)

# [VEGA-PATCH 9 T09:15 18 giu] Macro legacy FindHIP.cmake non disponibile su ROCm 6.x.
# [VEGA-PATCH 41 T15:35 23 giu — FIX ARCHITETTURALE CRITICO]
# Lo stub precedente `add_library(${ARGN})` causava CMake a IGNORARE i .hip files (211 files
# in native/hip/). Risultato: torch_hip.dll = guscio vuoto con SOLO .cpp wrappers, ZERO kernel
# CUDA nativi. Build #21-51 tutte compromesse dalla stessa causa. Vedi PYTORCH.md T15:30.
#
# Fix: enable_language(HIP) PRIMA dei macro stub, cosi' CMake riconosce nativamente .hip
# come HIP language e usa CMAKE_HIP_COMPILER (clang) per compilarli.
if(NOT COMMAND hip_include_directories)
  macro(hip_include_directories)
    include_directories(${ARGN})
  endmacro()
endif()

# Force enable HIP language se Marconi pack disponibile (richiede CMAKE_HIP_COMPILER env var)
if(WIN32 AND EXISTS "${ROCM_PATH}/compiler/bin/clang.exe" AND NOT CMAKE_HIP_COMPILER_LOADED)
  set(CMAKE_HIP_COMPILER "${ROCM_PATH}/compiler/bin/clang.exe" CACHE FILEPATH "HIP compiler" FORCE)
  set(CMAKE_HIP_ARCHITECTURES "${PYTORCH_ROCM_ARCH}" CACHE STRING "HIP target arch" FORCE)
  set(CMAKE_HIP_PLATFORM "amd" CACHE STRING "HIP platform" FORCE)
  # [VEGA-PATCH 41b T15:35] CMake CMakeDetermineHIPCompiler.cmake:174 richiede CMAKE_HIP_COMPILER_ROCM_ROOT
  # (cerca via hipconfig --rocmpath che Marconi pack non ha). Set esplicito.
  set(CMAKE_HIP_COMPILER_ROCM_ROOT "${ROCM_PATH}" CACHE PATH "ROCm root" FORCE)
  # [VEGA-PATCH 41c T15:38] Marconi pack device_libs in path NON standard. Passa --rocm-device-lib-path
  # esplicito a clang HIP (era: 'cannot find ROCm device library'). Vedi PYTORCH.md T15:38.
  # [VEGA-PATCH 46g T16:55 5 lug] -x hip OBBLIGATORIO: senza, clang-cl compila i .hip come C++ host
  # (threadIdx/blockDim undeclared). E' il muro su cui il build #62 si fermava (Sleep.hip). Con -x hip
  # clang-cl compila come HIP device code -> device builtin definiti.
  # [VEGA-PATCH 50 1 ago] -mcode-object-version=4 OBBLIGATORIO. Il clang 21 del Marconi pack
  # emette code object v6; il comgr del driver Adrenalin (clr 23.19, quello che vede la gfx906)
  # legge fino alla v4 e i suoi stessi blit kernel li compila in v4. Con la v6 ogni
  # hipLaunchKernel fallisce con hipErrorSharedObjectInitFailed, preceduto nel log da
  # "COMGR failed to get code object ISA name". Verificato con prova_kernel.hip:
  # COv4 -> kernel eseguito e risultati corretti; COv6 -> stesso errore di PyTorch.
  set(CMAKE_HIP_FLAGS_INIT "-x hip --rocm-path=${ROCM_PATH} --rocm-device-lib-path=${ROCM_PATH}/device_libs -mcode-object-version=4"
      CACHE STRING "HIP compile flags" FORCE)
  # [VEGA-PATCH 53 1 ago] CMAKE_HIP_FLAGS_RELEASE era VUOTO: clang-cl senza flag /O
  # compila a ottimizzazione ZERO. Tutti i kernel device e i loro wrapper host
  # risultavano non ottimizzati. Misurato prima della correzione: elementwise a
  # 4 GB/s contro i 489 della scheda, e 307 us per lancio contro i 46 di ZLUDA.
  # Il matmul non ne risentiva perche' lo esegue rocBLAS, gia' compilato altrove.
  # ATTENZIONE alla sintassi: il compilatore e' clang-CL, quindi vuole /O2 in stile
  # MSVC. La forma GCC -O3 viene ACCETTATA sulla riga di comando e poi SCARTATA
  # ("argument unused during compilation"), senza errore: si ottiene una build a
  # ottimizzazione zero credendo di averla ottimizzata. Misurato sullo stesso kernel:
  #   -O3 -> 15 GFLOPS,  6 GB/s        /O2 -> 1209 GFLOPS, 495 GB/s (banda piena)
  # NB: niente /DNDEBUG. c10/macros/Macros.h fa #undef NDEBUG per tenere vivo
  # CUDA_KERNEL_ASSERT; definendo NDEBUG si attiva il ramo che su Windows chiama
  # _wassert, e il link fallisce perche' qui la CRT e' statica (libucrt.lib) mentre
  # gli oggetti HIP la vogliono dllimport.
  set(CMAKE_HIP_FLAGS_RELEASE "/O2 /Ob2" CACHE STRING "HIP release flags" FORCE)
  set(CMAKE_HIP_FLAGS_RELWITHDEBINFO "/O2 /Ob1" CACHE STRING "HIP relwithdebinfo flags" FORCE)
  message(STATUS "[VEGA-PATCH 53] CMAKE_HIP_FLAGS_RELEASE=${CMAKE_HIP_FLAGS_RELEASE}")
  # [VEGA-PATCH 41d T15:45] Skip CMake HIP compiler ABI test che fail per clang lld lookup
  # (clang cerca 'lld' senza .exe, anche con lld.exe presente dice 'program not executable').
  # Settando CMAKE_HIP_COMPILER_FORCED=TRUE diciamo a CMake di accettare il compiler senza testarlo.
  # La build vera userà clang directly via custom rules.
  set(CMAKE_HIP_COMPILER_FORCED TRUE CACHE BOOL "Skip HIP compiler ABI test" FORCE)
  set(CMAKE_HIP_COMPILER_ID "Clang" CACHE STRING "HIP compiler ID" FORCE)
  set(CMAKE_HIP_COMPILER_VERSION "21.0.0" CACHE STRING "HIP compiler version" FORCE)
  # [VEGA-PATCH 41e T17:05] Build #56 ha LINKATO torch_cpu.dll 161 MB (milestone storico),
  # MA Sleep.hip fail per clang.exe (GNU style) che riceve flag MSVC (/nologo, -imsvc, /Fo, -fPIC).
  # Forziamo frontend variant MSVC → CMake genera flag MSVC compatibili con clang-cl.
  # IMPORTANTE: cambia anche CMAKE_HIP_COMPILER a clang-cl.exe che capisce sia HIP (-x hip)
  # sia flag MSVC nativamente.
  set(CMAKE_HIP_COMPILER "${ROCM_PATH}/compiler/bin/clang-cl.exe" CACHE FILEPATH "HIP compiler" FORCE)
  set(CMAKE_HIP_COMPILER_FRONTEND_VARIANT "MSVC" CACHE STRING "HIP compiler frontend" FORCE)
  set(CMAKE_HIP_SIMULATE_ID "MSVC" CACHE STRING "" FORCE)
  set(CMAKE_HIP_SIMULATE_VERSION "19.0" CACHE STRING "" FORCE)
  message(STATUS "[VEGA-PATCH 41] Marconi pack clang detected, forcing CMAKE_HIP_COMPILER=${CMAKE_HIP_COMPILER}")
  message(STATUS "[VEGA-PATCH 41b] CMAKE_HIP_COMPILER_ROCM_ROOT=${CMAKE_HIP_COMPILER_ROCM_ROOT}")
  message(STATUS "[VEGA-PATCH 41c] CMAKE_HIP_FLAGS_INIT=${CMAKE_HIP_FLAGS_INIT}")
  message(STATUS "[VEGA-PATCH 41d] CMAKE_HIP_COMPILER_FORCED=TRUE (skip ABI test)")
  enable_language(HIP)
  message(STATUS "[VEGA-PATCH 41] HIP language enabled, .hip files will be compiled natively")
endif()

if(NOT COMMAND hip_add_library)
  macro(hip_add_library)
    # [VEGA-PATCH 41] Ora che enable_language(HIP) e' attivo, add_library gestisce .hip nativamente
    add_library(${ARGN})
    # [VEGA-PATCH 43.1 T20:00 24 giu] FIX MSVC_RUNTIME_LIBRARY non riconosciuto per HIP compiler.
    # CMake 3.31 default CMP0091=NEW propaga MSVC_RUNTIME_LIBRARY=MultiThreadedDLL a tutti target
    # MSVC environment. Per HIP language, anche con FRONTEND_VARIANT=MSVC, CMake non considera
    # HIP compiler come supportante la property → Generate step error.
    # Fix: resettare property a stringa vuota sul target HIP (CMake skip check se property unset).
    # NOTA v43.1: usare ARGV0 (special var primo arg macro) invece di list(GET ARGN 0 ...)
    # perché in macro CMake ARGN è string-concat e list(GET) ritorna NOTFOUND.
    # Guard if(TARGET) per non rompere su chiamate senza target name valido.
    if(TARGET ${ARGV0})
      set_target_properties(${ARGV0} PROPERTIES MSVC_RUNTIME_LIBRARY "")
      message(STATUS "[VEGA-PATCH 43.1] hip_add_library(${ARGV0}): MSVC_RUNTIME_LIBRARY reset")
    endif()
  endmacro()
endif()
if(NOT COMMAND hip_add_executable)
  macro(hip_add_executable)
    add_executable(${ARGN})
  endmacro()
endif()

# [VEGA-PATCH 4 T08:20 18 giu] HIP_FOUND non viene impostato correttamente da find_package(HIP) su Windows
# anche se hip-config.cmake viene trovato (ROCm 6.4 lib/cmake/hip). Forziamo PYTORCH_FOUND_HIP=TRUE
# se hip-config è stato letto, per consentire la build prosegua.
if(NOT HIP_FOUND)
  if(EXISTS "$ENV{HIP_PATH}/lib/cmake/hip/hip-config.cmake" OR EXISTS "${ROCM_PATH}/lib/cmake/hip/hip-config.cmake")
    message(STATUS "[VEGA-PATCH 4] HIP_FOUND not set but hip-config exists, forcing PYTORCH_FOUND_HIP=TRUE")
    set(HIP_FOUND TRUE)
  elseif(WIN32 AND EXISTS "${ROCM_PATH}/include/hip")
    # [VEGA-PATCH 4b T03:20 20 giu] Marconi 5.7 Expansion Pack ad-hoc — NO struttura lib/cmake/hip standard.
    # Headers HIP esistono in include/hip → sufficienti per build PyTorch + linking amdhip64.
    message(STATUS "[VEGA-PATCH 4b] Marconi pack rilevato (include/hip esiste), forcing HIP_FOUND=TRUE")
    set(HIP_FOUND TRUE)
  endif()
endif()

if(HIP_FOUND)
  set(PYTORCH_FOUND_HIP TRUE)
  set(FOUND_ROCM_VERSION_H FALSE)

  set(PROJECT_RANDOM_BINARY_DIR "${PROJECT_BINARY_DIR}")
  set(file "${PROJECT_BINARY_DIR}/detect_rocm_version.cc")

  # Find ROCM version for checks
  # ROCM 5.0 and later will have header api for version management
  if(EXISTS ${ROCM_INCLUDE_DIRS}/rocm_version.h)
    set(FOUND_ROCM_VERSION_H TRUE)
    file(WRITE ${file} ""
      "#include <rocm_version.h>\n"
      )
  elseif(EXISTS ${ROCM_INCLUDE_DIRS}/rocm-core/rocm_version.h)
    set(FOUND_ROCM_VERSION_H TRUE)
    file(WRITE ${file} ""
      "#include <rocm-core/rocm_version.h>\n"
      )
  else()
    message("********************* rocm_version.h couldnt be found ******************\n")
  endif()

  if(FOUND_ROCM_VERSION_H)
    file(APPEND ${file} ""
      "#include <cstdio>\n"

      "#ifndef ROCM_VERSION_PATCH\n"
      "#define ROCM_VERSION_PATCH 0\n"
      "#endif\n"
      "#define STRINGIFYHELPER(x) #x\n"
      "#define STRINGIFY(x) STRINGIFYHELPER(x)\n"
      "int main() {\n"
      "  printf(\"%d.%d.%s\", ROCM_VERSION_MAJOR, ROCM_VERSION_MINOR, STRINGIFY(ROCM_VERSION_PATCH));\n"
      "  return 0;\n"
      "}\n"
      )

    try_run(run_result compile_result ${PROJECT_RANDOM_BINARY_DIR} ${file}
      CMAKE_FLAGS "-DINCLUDE_DIRECTORIES=${ROCM_INCLUDE_DIRS}"
      RUN_OUTPUT_VARIABLE rocm_version_from_header
      COMPILE_OUTPUT_VARIABLE output_var
      )
    # We expect the compile to be successful if the include directory exists.
    if(NOT compile_result)
      message(FATAL_ERROR "Caffe2: Couldn't determine version from header: " ${output_var})
    endif()
    message(STATUS "Caffe2: Header version is: " ${rocm_version_from_header})
    set(ROCM_VERSION_DEV_RAW ${rocm_version_from_header})
    message("\n***** ROCm version from rocm_version.h ****\n")
  endif()

  # [VEGA-PATCH 5b T08:30] skip REGEX se RAW vuoto (try_run fallita su Windows, valori forzati downstream)
  if(ROCM_VERSION_DEV_RAW)
    string(REGEX MATCH "^([0-9]+)\.([0-9]+)\.([0-9]+).*$" ROCM_VERSION_DEV_MATCH ${ROCM_VERSION_DEV_RAW})
  else()
    set(ROCM_VERSION_DEV_MATCH "")
  endif()

  if(ROCM_VERSION_DEV_MATCH)
    set(ROCM_VERSION_DEV_MAJOR ${CMAKE_MATCH_1})
    set(ROCM_VERSION_DEV_MINOR ${CMAKE_MATCH_2})
    set(ROCM_VERSION_DEV_PATCH ${CMAKE_MATCH_3})
    set(ROCM_VERSION_DEV "${ROCM_VERSION_DEV_MAJOR}.${ROCM_VERSION_DEV_MINOR}.${ROCM_VERSION_DEV_PATCH}")
    math(EXPR ROCM_VERSION_DEV_INT "(${ROCM_VERSION_DEV_MAJOR}*10000) + (${ROCM_VERSION_DEV_MINOR}*100) + ${ROCM_VERSION_DEV_PATCH}")
  endif()

  # [VEGA-PATCH 5 T08:25 18 giu] Fallback ROCM_VERSION quando rocm_version.h parsing fail
  # ROCm 6.4 install ha hip-config con version 6.4.50101, ma try_compile rocm_version.h fail su Windows.
  # Forziamo default per ROCm 6.4.
  if(NOT ROCM_VERSION_DEV)
    set(ROCM_VERSION_DEV_MAJOR 6)
    set(ROCM_VERSION_DEV_MINOR 4)
    set(ROCM_VERSION_DEV_PATCH 1)
    set(ROCM_VERSION_DEV "6.4.1")
    set(ROCM_VERSION_DEV_INT 60401)
    message(STATUS "[VEGA-PATCH 5] ROCM_VERSION forzato a 6.4.1 (default fallback)")
  endif()
  if(NOT HIP_VERSION_MAJOR)
    set(HIP_VERSION_MAJOR 6)
    set(HIP_VERSION_MINOR 4)
    message(STATUS "[VEGA-PATCH 5] HIP_VERSION forzato a 6.4")
  endif()

  message("ROCM_VERSION_DEV: ${ROCM_VERSION_DEV}")
  message("ROCM_VERSION_DEV_MAJOR: ${ROCM_VERSION_DEV_MAJOR}")
  message("ROCM_VERSION_DEV_MINOR: ${ROCM_VERSION_DEV_MINOR}")
  message("ROCM_VERSION_DEV_PATCH: ${ROCM_VERSION_DEV_PATCH}")
  message("ROCM_VERSION_DEV_INT:   ${ROCM_VERSION_DEV_INT}")

  math(EXPR TORCH_HIP_VERSION "(${HIP_VERSION_MAJOR} * 100) + ${HIP_VERSION_MINOR}")
  message("HIP_VERSION_MAJOR: ${HIP_VERSION_MAJOR}")
  message("HIP_VERSION_MINOR: ${HIP_VERSION_MINOR}")
  message("TORCH_HIP_VERSION: ${TORCH_HIP_VERSION}")

  message("\n***** Library versions from dpkg *****\n")
  execute_process(COMMAND dpkg -l COMMAND grep rocm-dev COMMAND awk "{print $2 \" VERSION: \" $3}")
  execute_process(COMMAND dpkg -l COMMAND grep rocm-libs COMMAND awk "{print $2 \" VERSION: \" $3}")
  execute_process(COMMAND dpkg -l COMMAND grep hsakmt-roct COMMAND awk "{print $2 \" VERSION: \" $3}")
  execute_process(COMMAND dpkg -l COMMAND grep rocr-dev COMMAND awk "{print $2 \" VERSION: \" $3}")
  execute_process(COMMAND dpkg -l COMMAND grep -w hcc COMMAND awk "{print $2 \" VERSION: \" $3}")
  execute_process(COMMAND dpkg -l COMMAND grep hip-base COMMAND awk "{print $2 \" VERSION: \" $3}")
  execute_process(COMMAND dpkg -l COMMAND grep hip_hcc COMMAND awk "{print $2 \" VERSION: \" $3}")

  message("\n***** Library versions from cmake find_package *****\n")

  set(CMAKE_HIP_CLANG_FLAGS_DEBUG ${CMAKE_CXX_FLAGS_DEBUG})
  set(CMAKE_HIP_CLANG_FLAGS_RELEASE ${CMAKE_CXX_FLAGS_RELEASE})
  ### Remove setting of Flags when FindHIP.CMake PR #558 is accepted.###

  # [VEGA-PATCH 46 T11:25 5 lug - REGOLA 4-bis: SOLO ROCm 5.7 + Marconi]
  # I 12 pacchetti config risolti da ROCm 5.7 base (config+import-lib+prefix coerenti e intatti).
  # hipblaslt+hipblas-common dai NOSTRI artifact TheRock 7.14 (binari sovrani, non da 7.1).
  # hsa-runtime64/amd_comgr/AMDDeviceLibs restano su Marconi (ROCM_PATH): se find_package fallisce
  # si creano stub config dentro Marconi (aggiungere a Marconi cio' che manca).
  set(ROCM57_BASE "C:/Program Files/AMD/ROCm/5.7")
  set(THEROCK_BLAS "C:/TheRock_workspace/TheRock/build_gfx906/artifacts/blas_dev_generic/math-libs/BLAS")
  # [VEGA-PATCH 46c T11:40 5 lug] dist/rocm = install TheRock 7.14 COMPLETO (cmake+lib+dll+header
  # coerenti sotto un unico prefix). Gli stage dev split hanno le import-lib ma NON le dll (config
  # -targets-release fallisce su bin/rocblas.dll mancante). dist/rocm ha tutto -> fonte unica BLAS.
  set(THEROCK_DIST "C:/TheRock_workspace/TheRock/build_gfx906/dist/rocm")
  set(hip_DIR ${ROCM57_BASE}/lib/cmake/hip)
  set(hsa-runtime64_DIR ${ROCM_PATH}/lib/cmake/hsa-runtime64)
  set(AMDDeviceLibs_DIR ${ROCM_PATH}/lib/cmake/AMDDeviceLibs)
  set(amd_comgr_DIR ${ROCM_PATH}/lib/cmake/amd_comgr)
  set(rocrand_DIR ${ROCM57_BASE}/lib/cmake/rocrand)
  set(hiprand_DIR ${ROCM57_BASE}/lib/cmake/hiprand)
  # [VEGA-PATCH 46b T11:35 5 lug] Famiglia BLAS COERENTE a TheRock 7.14 (nostri artifact gfx906):
  # hipblas.h 5.7 ridefinisce hipblasOperation_t inline -> collide con hipblas-common.h 7.x
  # (incluso da hipblaslt 7.14). Allineando rocblas+hipblas a TheRock 7.14, hipblas.h fa
  # #include <hipblas-common/hipblas-common.h> senza ridefinire -> zero conflitto.
  set(rocblas_DIR ${THEROCK_DIST}/lib/cmake/rocblas)
  set(hipblas_DIR ${THEROCK_DIST}/lib/cmake/hipblas)
  set(hipblaslt_DIR ${THEROCK_DIST}/lib/cmake/hipblaslt)
  set(hipblas-common_DIR ${THEROCK_DIST}/lib/cmake/hipblas-common)
  set(miopen_DIR ${ROCM_PATH}/lib/cmake/miopen)
  set(rocfft_DIR ${ROCM57_BASE}/lib/cmake/rocfft)
  set(hipfft_DIR ${ROCM57_BASE}/lib/cmake/hipfft)
  set(hipsparse_DIR ${ROCM57_BASE}/lib/cmake/hipsparse)
  set(rccl_DIR ${ROCM_PATH}/lib/cmake/rccl)
  # [VEGA-PATCH 46f T14:00 5 lug] rocprim/hipcub/rocthrust 7.1 copiati IN Marconi (header-only):
  # i 5.7 usano ::rocprim::half non definito con clang 21 -> non compilano. I 7.1 (using half =
  # ::__half) sono coerenti. Copiati in Marconi/include + lib/cmake (aggiungere a Marconi cio' che manca).
  set(rocprim_DIR ${ROCM_PATH}/lib/cmake/rocprim)
  set(hipcub_DIR ${ROCM_PATH}/lib/cmake/hipcub)
  set(rocthrust_DIR ${ROCM_PATH}/lib/cmake/rocthrust)
  set(hipsolver_DIR ${ROCM57_BASE}/lib/cmake/hipsolver)
  set(hiprtc_DIR ${ROCM57_BASE}/lib/cmake/hiprtc)


  find_package_and_print_version(hip REQUIRED)
  find_package_and_print_version(hsa-runtime64 REQUIRED)
  find_package_and_print_version(amd_comgr REQUIRED)
  find_package_and_print_version(rocrand REQUIRED)
  find_package_and_print_version(hiprand REQUIRED)
  find_package_and_print_version(rocblas REQUIRED)
  find_package_and_print_version(hipblas REQUIRED)
  find_package_and_print_version(hipblaslt REQUIRED)
  find_package_and_print_version(miopen REQUIRED)
  find_package_and_print_version(hipfft REQUIRED)
  find_package_and_print_version(hipsparse REQUIRED)
  find_package_and_print_version(rccl)
  find_package_and_print_version(rocprim REQUIRED)
  find_package_and_print_version(hipcub REQUIRED)
  find_package_and_print_version(rocthrust REQUIRED)
  find_package_and_print_version(hipsolver REQUIRED)
  find_package_and_print_version(hiprtc REQUIRED)


  # [VEGA-PATCH 49 1 ago] Il Marconi pack contiene DUE import library per HIP:
  #   lib/amdhip64.lib         -> importa da amdhip64_6.dll  (copiata da ROCm 6.x)
  #   lib/import/amdhip64.lib  -> importa da amdhip64.dll    (runtime Adrenalin 5.7)
  # Il runtime che vede davvero la gfx906 e' amdhip64.dll (Adrenalin): con il nome _6
  # servirebbe un proxy, che pero' ha 43 funzioni stub e va in access violation
  # nell'allocazione. Cerchiamo quindi PRIMA in lib/import.
  find_library(PYTORCH_HIP_LIBRARIES amdhip64
    HINTS ${ROCM_PATH}/lib/import ${ROCM_PATH}/lib
    NO_DEFAULT_PATH)
  find_library(PYTORCH_HIP_LIBRARIES amdhip64 HINTS ${ROCM_PATH}/lib)
  message(STATUS "[VEGA-PATCH 49] PYTORCH_HIP_LIBRARIES = ${PYTORCH_HIP_LIBRARIES}")
  # TODO: miopen_LIBRARIES should return fullpath to the library file,
  # however currently it's just the lib name
  if(TARGET ${miopen_LIBRARIES})
    set(PYTORCH_MIOPEN_LIBRARIES ${miopen_LIBRARIES})
  else()
    find_library(PYTORCH_MIOPEN_LIBRARIES ${miopen_LIBRARIES} HINTS ${ROCM_PATH}/lib)
  endif()
  # TODO: rccl_LIBRARIES should return fullpath to the library file,
  # however currently it's just the lib name
  if(TARGET ${rccl_LIBRARIES})
    set(PYTORCH_RCCL_LIBRARIES ${rccl_LIBRARIES})
  else()
    find_library(PYTORCH_RCCL_LIBRARIES ${rccl_LIBRARIES} HINTS ${ROCM_PATH}/lib)
  endif()
  find_library(ROCM_HIPRTC_LIB hiprtc HINTS ${ROCM_PATH}/lib)
  # roctx is part of roctracer
  find_library(ROCM_ROCTX_LIB roctx64 HINTS ${ROCM_PATH}/lib)
  # [VEGA-PATCH 10 T09:33 18 giu] Su Windows ROCm 6.4 roctx64 NON è distribuito.
  # Stub vuoto invece di NOTFOUND per evitare CMake Generate fail su link torch_python.
  if(NOT ROCM_ROCTX_LIB)
    message(STATUS "[VEGA-PATCH 10] ROCM_ROCTX_LIB not found, set to empty (Windows ROCm 6.4)")
    set(ROCM_ROCTX_LIB "")
  endif()
  if(NOT ROCM_HIPRTC_LIB)
    set(ROCM_HIPRTC_LIB "")
  endif()

  # check whether HIP declares new types
  set(file "${PROJECT_BINARY_DIR}/hip_new_types.cc")
  file(WRITE ${file} ""
    "#include <hip/library_types.h>\n"
    "int main() {\n"
    "    hipDataType baz = HIP_R_8F_E4M3_FNUZ;\n"
    "    return 0;\n"
    "}\n"
    )

  try_compile(hip_compile_result ${PROJECT_RANDOM_BINARY_DIR} ${file}
    CMAKE_FLAGS "-DINCLUDE_DIRECTORIES=${ROCM_INCLUDE_DIRS}"
    COMPILE_DEFINITIONS -D__HIP_PLATFORM_AMD__ -D__HIP_PLATFORM_HCC__
    OUTPUT_VARIABLE hip_compile_output)

  if(hip_compile_result)
    set(HIP_NEW_TYPE_ENUMS ON)
    #message("HIP is using new type enums: ${hip_compile_output}")
    message("HIP is using new type enums")
  else()
    set(HIP_NEW_TYPE_ENUMS OFF)
    #message("HIP is NOT using new type enums: ${hip_compile_output}")
    message("HIP is NOT using new type enums")
  endif()

endif()
