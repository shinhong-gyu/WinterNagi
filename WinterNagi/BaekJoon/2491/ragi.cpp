#include <iostream>
#include <vector>
#include <deque>

using namespace std;

int main()
{
    int N = 0;

    cin >> N;

    vector<int> arr(N);
    int count = 0;
    int max_count = 0;

    int prev = -1;
    for (int& a : arr)
    {
        cin >> a;
        if (prev <= a)
        {
            count = count + 1;
        }
        else
        {
            count = 1;
        }
        max_count = count > max_count ? count : max_count;
        prev = a;
    }

    deque<int> deq;

    count = 0;

    for (vector<int>::reverse_iterator it = arr.rbegin(); it != arr.rend(); ++it)
    {
        if (deq.empty())
        {
            deq.push_front(*it);
            count = count + 1;
        }
        else if (*it >= deq.front())
        {
            count = count + 1;
            deq.push_front(*it);
            while (*it < deq.back())
            {
                deq.pop_back();
                count = count - 1;
            }
        }
        else
        {
            while (!deq.empty())
            {
                deq.pop_back();
            }
            deq.push_front(*it);
            count = 1;
        }
        max_count = count > max_count ? count : max_count;
        prev = *it;
    }

    cout << max_count << '\n';
    return (0);
}
