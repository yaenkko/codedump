#include <iostream>
#include <string>

using namespace std;

int main() {
    int i;
    cout << "Wie alt bist du? " << endl;
    cin >> i;
    if (cin.fail()) {
        cout << "Das ist keine Zahl." << endl;
        return 0;
    } else {
        cout << "Du bist " << i << " Jahre alt." << endl;
    }
    return i;
}