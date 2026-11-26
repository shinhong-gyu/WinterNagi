#include <iostream>
#include <vector>

using namespace std;

int main()
{
	ios::sync_with_stdio(false);
	cin.tie(NULL);
	cout.tie(NULL);

	int N, K;

	cin >> N >> K;

	vector<int> buckets(26);

	buckets[1] = N;

	int curBucketNum = N;
	int buy = 0;

	int minBucketIdx = 1;

	while (curBucketNum > K)
	{
		for (int i = minBucketIdx; i < 25 && buckets[i] >= 2; i++)
		{
			int cnt = buckets[i] / 2;
			buckets[i] %= 2;
			buckets[i + 1] += cnt;
			curBucketNum -= cnt;
		}

		if (curBucketNum <= K)
		{
			break;
		}

		int i = 1;

		while (buckets[minBucketIdx] == 0)
		{
			minBucketIdx++;
		}

		buckets[minBucketIdx]++;
		curBucketNum++;
		buy += (1 << (minBucketIdx - 1));
	}

	cout << buy;
}