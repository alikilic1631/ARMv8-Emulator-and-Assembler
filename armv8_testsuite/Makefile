TEST_DIR ?= ./test
TEST_ACT_DIR = $(TEST_DIR)/actual_results


.PHONY: all test clean server

all: clean
	./run -pf

server:
	@echo "Starting server..."
	. ./.venv/bin/activate &&\
	python3 -m flask --app armv8server.app run

TO_CLEAN = $(filter-out %.json, $(wildcard $(TEST_ACT_DIR)/*))
clean:
	$(RM) -rf $(TO_CLEAN)

# You can safely ignore this ;)
-include non_student/Makefile
