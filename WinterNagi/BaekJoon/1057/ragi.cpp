#include <iostream>

using namespace std;

int main()
{
	int N = 0;
	cin >> N;

	int a, b = 0;
	cin >> a >> b;

	if (a > b)
	{
		int memo = a;
		a = b;
		b = memo;
	}
	int round = 1;

	while (N != 0)
	{
		if (a & 1)
		{
			if (a + 1 == b)
			{
				cout << round << '\n';
				return (0);
			}
		}
		round = round + 1;
		if (N != 1 && (N & 1))
		{
			N = N + 1;
		}
		N = N / 2;
		a = a / 2 + (a & 1 ? 1 : 0);
		b = b / 2 + (b & 1 ? 1 : 0);
	}

	cout << "-1" << '\n';
	return (0);
}
