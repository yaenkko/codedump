#include <iostream>
#include <cstdlib>
#include <ctime>
// this code here needs some work, not working to my liking 
class GuessingGame {
private:
    int secretNumber;
    int maxNumber;
    int prize;

public:
    GuessingGame(int difficulty) {
        maxNumber = difficulty * 10;
        prize = difficulty * 100;
        std::srand(std::time(0)); // randomizer init
        secretNumber = std::rand() % maxNumber + 1; //random nmbr
    }

    void play() {
        int guess;
        std::cout << "Welcome to  Luigis Casino! Guess a number between 1 and  " << maxNumber << ".\n";
        while (true) {
            std::cout << "Take a guess: ";
            std::cin >> guess;
            if (guess == secretNumber) {
                std::cout << "You win " << prize << " Dollar.\n";
                break;
            }
            else if (guess < secretNumber) {
                std::cout << "Too low. Try again.\n";
            }
            else {
                std::cout << "Too high.Try again.\n";
            }
        }
    }
};

int main() {
    int difficulty;
    std::cout << "Choose difficulty (1-3): ";
    std::cin >> difficulty;

    GuessingGame game(difficulty);
    game.play();

    return 0;
}
