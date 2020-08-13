NAME=bms1

$(NAME): $(NAME).py
	cp $(NAME).py $(NAME)
	chmod +x $(NAME)

clean:
	rm -f $(NAME)

run:
	./$(NAME) multiplex.ts

# 	./$(NAME) input 20 > output20

# 	./$(NAME) input 13 > output13

# 	./$(NAME) input > output1

# 	diff output8 pattern8

# 	diff output20 pattern20

# 	diff output13 pattern13

# 	diff output1 pattern1
