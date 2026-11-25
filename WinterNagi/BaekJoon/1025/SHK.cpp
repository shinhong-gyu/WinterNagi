#include <iostream>
#include <vector>
#include <string>
#include <cmath>

using namespace std;

int N, M;

bool IsInXRange(int x)
{
	return (x >= 0 && x < M);
}

bool IsInYRange(int y)
{
	return (y >= 0 && y < N);
}

bool IsSquare(int num)
{
	if (num < 0)
	{
		return false;
	}

	int root = (int)sqrt(num);
	return (root * root == num);
}

int main()
{
	ios::sync_with_stdio(false);
	cin.tie(NULL);
	cout.tie(NULL);

	int maxSquare = -1;

	cin >> N >> M;

	vector<vector<int>> table(N, vector<int>(M));

	for (int i = 0; i < N; i++)
	{
		string num;
		cin >> num;
		for (int j = 0; j < M; j++)
		{
			table[i][j] = num[j] - '0';
		}
	}

	// dx , dy
	int dx[8] = { 0, 1, 0, -1, 1, 1, -1, -1 };
	int dy[8] = { 1, 0, -1, 0, 1, -1, 1, -1 };


	// y,x에서 부터 시작한 수열이 제곱수인지 확인
	for (int y = 0; y < N; y++)
	{
		for (int x = 0; x < M; x++)
		{
			// 방향은 8가지
			for (int i = 0; i < 8; i++)
			{
				// 등차 수열의 간격
				for (int n1 = 1; n1 <= 9; n1++)
				{
					for (int n2 = 1; n2 <= 9; n2++)
					{
						int ny = y;
						int nx = x;

						int num = table[y][x];

						if (IsSquare(num))
						{
							maxSquare = max(maxSquare, num);
						}

						while (true)
						{
							// y,x에서 nx,ny 만큼 이동한 좌표를 이어붙임
							ny = ny + n1 * dy[i];
							nx = nx + n2 * dx[i];

							if (!IsInXRange(nx) || !IsInYRange(ny))
							{
								break;
							}

							num = num * 10 + table[ny][nx];

							if (IsSquare(num))
							{
								maxSquare = max(maxSquare, num);
							}
						}
					}
				}
			}
		}
	}

	cout << maxSquare << "\n";
}