CXX ?= clang++
CXXFLAGS ?= -std=c++17 -Wall -Wextra

all: app

app: main.cpp
	$(CXX) $(CXXFLAGS) -o app main.cpp

clean:
	rm -f app
