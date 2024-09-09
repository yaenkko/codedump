#include <iostream>
#include <cstdlib>
#include <ctime>

using namespace std;

int main() {
    cout << "Lets play some Rock, Paper, Scissors" << endl;
    cout << "Enter your choice (rock, paper, or scissors): ";
    string userChoice;
    cin >> userChoice;

    // generate rndm number for the bot
    srand(time(0));
    int randomChoice = rand() % 3;
    string computerChoice;
    if (randomChoice == 0) {
        computerChoice = "rock";
    }
    else if (randomChoice == 1) {
        computerChoice = "paper";
    }
    else {
        computerChoice = "scissors";
    }

    cout << "Computer chose: " << computerChoice << endl;

    // decide winner
    if (userChoice == computerChoice) {
        cout << "It's a tie!" << endl;
    }
    else if ((userChoice == "rock" && computerChoice == "scissors") ||
        (userChoice == "paper" && computerChoice == "rock") ||
        (userChoice == "scissors" && computerChoice == "paper")) {
        cout << "Kung Lao wins. Flawless victory." << endl;
    }
    else {
        cout << "Computer wins, fatality." << endl;
    }

    return 0;
}
