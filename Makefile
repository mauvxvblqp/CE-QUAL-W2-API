
FC ?= ifx
# Core compile flags for Intel ifx (LLVM-based Fortran)
FFLAGS ?= -c -fpp -recursive -DCLI_ONLY -fpe1 -O3

# Output directories for objects and module files
OBJDIR ?= build/obj
MODDIR ?= build/mod
MODFLAGS := -module $(MODDIR) -I $(MODDIR)

# Fortran module dependencies are not explicitly tracked; build sequentially
.NOTPARALLEL:

# Attempt to derive Intel oneAPI compiler lib dir from FC when FC ends with /bin/ifx
IFX_LIBDIR ?=
ifneq (,$(findstring /bin/ifx,$(FC)))
  IFX_LIBDIR := $(patsubst %/bin/ifx,%/lib,$(FC))
endif

# Linker flags (override or extend via environment)
LDFLAGS ?=
LDLIBS ?=

# Add rpath and -L for Intel compiler libs when detected; mark noexecstack to silence linker warning
ifneq ($(strip $(IFX_LIBDIR)),)
  LDFLAGS += -Wl,-rpath,$(IFX_LIBDIR) -L$(IFX_LIBDIR)
endif
# Allow a custom RPATH to be injected (colon-separated list supported)
W2_RPATH ?=
ifneq ($(strip $(W2_RPATH)),)
  LDFLAGS += -Wl,-rpath,$(W2_RPATH)
endif
LDFLAGS += -Wl,-z,noexecstack

# OPENMP not working properly, disabling these flags for now
# For ifx, consider: -qopenmp and -qmkl when enabling in future
# OPENMP_FLAGS=-qopenmp -qmkl
PREPROCESS_DEFS=preprocessor_definitions.fpp
MODULE_SOURCES=w2modules.f90

# original sources may need to be renamed using: rename 'y/ /_/'

SOURCES= \
        CEMA_Bubbles_Code_01.f90 \
        CEMA_FFT_Layer_01.f90 \
        CEMA_Input_01.f90 \
        CEMA_Input_Files_Read_01.f90 \
        CEMA_Output_01.f90 \
        CEMA_Sediment_Flux_Model_04.f90 \
        CEMA_Sediment_Model_03.f90 \
        CEMA_Turbidity_01.f90 \
        aerate.f90 \
        az.f90 \
        balances.f90 \
        date.f90 \
        density.f90 \
        endsimulation.f90 \
        envir_perf.f90 \
        fishhabitat.f90 \
        gas-transfer.f90 \
        gate-spill-pipe.f90 \
        heat-exchange.f90 \
        hydroinout.f90 \
        init-cond.f90 \
        init-geom.f90 \
        init-u-elws.f90 \
        init.f90 \
        input.f90 \
        layeraddsub.f90 \
        macrophyte-aux.f90 \
        output.f90 \
        outputa2w2tools.f90 \
        outputinitw2tools.f90 \
        particle.f90 \
        restart.f90 \
        screen_output_intel.f90 \
        shading.f90 \
        tdg.f90 \
        temperature.f90 \
        time-varying-data.f90 \
        transport.f90 \
        update.f90 \
        w2_4_win.f90 \
        water-quality.f90 \
        waterbody.f90 \
        withdrawal.f90 \
        wqconstituents.f90 \
        progress_cli.f90 \
        diagnostics_cli.f90

preprocess_def_objects=$(patsubst %.fpp,$(OBJDIR)/%.o,$(PREPROCESS_DEFS))
objects=$(patsubst %.f90,$(OBJDIR)/%.o,$(SOURCES))


.PHONY: renames
renames:
	@# Convert .F90 to .f90 (portable, no external rename needed)
	@for f in *.F90; do \
		[ -e "$$f" ] || continue; \
		nf="$${f%.*}.f90"; \
		if [ "$$f" != "$$nf" ]; then \
			if [ -e "$$nf" ]; then echo "skip $$f -> $$nf (exists)"; else mv "$$f" "$$nf"; fi; \
		fi; \
	done
	@# Replace spaces with underscores in Fortran source filenames
	@for f in *.[fF]90; do \
		[ -e "$$f" ] || continue; \
		case "$$f" in *" "*) \
			nf=$$(printf '%s' "$$f" | tr ' ' '_'); \
			if [ -e "$$nf" ] && [ "$$f" != "$$nf" ]; then echo "skip $$f -> $$nf (exists)"; else mv "$$f" "$$nf"; fi ;; \
		esac; \
	done

.PHONY: w2modules clean
$(OBJDIR) $(MODDIR):
	@mkdir -p $@

w2modules: $(OBJDIR)/w2modules.o

$(OBJDIR)/w2modules.o: $(MODULE_SOURCES) | $(OBJDIR) $(MODDIR)
	$(FC) $(FFLAGS) $(MODFLAGS) -o $@ $<

t1: w2modules
	echo "done with modules"

w2_exe_linux: w2modules $(preprocess_def_objects) $(objects)
	$(FC) $(LDFLAGS) -o w2_exe_linux $(objects) $(OBJDIR)/w2modules.o $(OBJDIR)/preprocessor_definitions.o $(LDLIBS)

# Ensure module build order where needed
$(OBJDIR)/w2_4_win.o: $(OBJDIR)/progress_cli.o $(OBJDIR)/diagnostics_cli.o


clean:
	rm -rf $(OBJDIR) $(MODDIR)

$(OBJDIR)/%.o : %.f90 | $(OBJDIR) $(MODDIR)
	$(FC) $(FFLAGS) $(MODFLAGS) -o $@ $<

$(OBJDIR)/%.o : %.fpp | $(OBJDIR) $(MODDIR)
	$(FC) $(FFLAGS) $(MODFLAGS) -o $@ $<
