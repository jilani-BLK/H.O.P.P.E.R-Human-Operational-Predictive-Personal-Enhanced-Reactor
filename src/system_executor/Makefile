CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c11
LDFLAGS = -lmicrohttpd -lcjson
TARGET = build/system_executor
SRCDIR = src
BUILDDIR = build
SOURCES = $(wildcard $(SRCDIR)/*.c)
OBJECTS = $(SOURCES:$(SRCDIR)/%.c=$(BUILDDIR)/%.o)

.PHONY: all clean

all: $(TARGET)

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

$(TARGET): $(BUILDDIR) $(OBJECTS)
	$(CC) $(OBJECTS) -o $(TARGET) $(LDFLAGS)

$(BUILDDIR)/%.o: $(SRCDIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -rf $(BUILDDIR)

run: $(TARGET)
	./$(TARGET)
