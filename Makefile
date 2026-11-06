CONTIKI_PROJECT = udp-client udp-server
all: $(CONTIKI_PROJECT)

PROJECT_CONF_PATH = project-conf.h

CONTIKI ?= ../..
include $(CONTIKI)/Makefile.include
