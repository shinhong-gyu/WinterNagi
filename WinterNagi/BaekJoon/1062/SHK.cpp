//#include <iostream>
//#include <vector>
//#include <string>
//#include <algorithm>
//#include <unordered_map>
//#include <unordered_set>
//
//using namespace std;
//
//vector<string> words;
//unordered_map<char, bool> learn;
//
//int maxLearn = 0;
//
//void RemoveANTIC(string& word)
//{
//	word.erase(remove(word.begin(), word.end(), 'a'), word.end());
//	word.erase(remove(word.begin(), word.end(), 'n'), word.end());
//	word.erase(remove(word.begin(), word.end(), 't'), word.end());
//	word.erase(remove(word.begin(), word.end(), 'i'), word.end());
//	word.erase(remove(word.begin(), word.end(), 'c'), word.end());
//}
//
//string RemoveDuplicates(string word)
//{
//	string result = "";
//	for (char c : word)
//	{
//		// result에 해당 문자가 아직 없으면 추가
//		if (result.find(c) == string::npos)
//		{
//			result += c;
//		}
//	}
//	return result;
//}
//
//string RemoveLearned(string word)
//{
//	string result = "";
//	for (char c : word)
//	{
//		if (!learn[c])
//		{
//			result += c;
//		}
//	}
//
//	return result;
//}
//
//bool CanRead(string word)
//{
//	for (char c : word)
//	{
//		if (!learn[c])
//		{
//			return false;
//		}
//	}
//	return true;
//}
//
//void Learning(int k, int i, int curLearn)
//{
//	if (i >= words.size())
//	{
//		maxLearn = max(maxLearn, curLearn);
//		return;
//	}
//
//	string temp = RemoveLearned(words[i]);
//
//	if (temp.length() == 0)
//	{
//		Learning(k, i + 1, curLearn + 1);
//	}
//	else if (temp.length() > k)
//	{
//		Learning(k, i + 1, curLearn);
//	}
//	else
//	{
//		for (int i = 0; i < temp.length(); i++)
//		{
//			learn[temp[i]] = true;
//		}
//
//		Learning(k - temp.length(), i + 1, curLearn + 1);
//
//		for (int i = 0; i < temp.length(); i++)
//		{
//			learn[temp[i]] = false;
//		}
//
//		Learning(k, i + 1, curLearn);
//	}
//}
//
//
//int main()
//{
//	ios::sync_with_stdio(false);
//	cin.tie(NULL);
//	cout.tie(NULL);
//
//	int N, K;
//
//	cin >> N >> K;
//
//	learn['a'] = true;
//	learn['n'] = true;
//	learn['t'] = true;
//	learn['i'] = true;
//	learn['c'] = true;
//
//	// anta 랑 tica를 제외한 단어가 몇 글자인지 확인
//
//	// 이미 배운 알파벳인지 확인
//
//	// 아직 안 배운 알파벳이라면 
//
//	int cnt = 0;
//
//	for (int i = 0; i < N; i++)
//	{
//		string temp;
//		cin >> temp;
//
//		RemoveANTIC(temp);
//		temp = RemoveDuplicates(temp);
//
//		if (temp.length() != 0)
//		{
//			words.emplace_back(temp);
//		}
//		else
//		{
//			cnt++;
//		}
//	}
//
//	if (K < 5)
//	{
//		cout << 0;
//		return 0;
//	}
//
//	if (K == 5)
//	{
//		cout << cnt;
//		return 0;
//	}
//
//	if (K == 26)
//	{
//		cout << N;
//		return 0;
//	}
//
//	K -= 5;
//
//	Learning(K, 0, cnt);
//
//	cout << maxLearn + diff;
//}


#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <unordered_set>

using namespace std;

void RemoveANTIC(string& word)
{
	word.erase(remove(word.begin(), word.end(), 'a'), word.end());
	word.erase(remove(word.begin(), word.end(), 'n'), word.end());
	word.erase(remove(word.begin(), word.end(), 't'), word.end());
	word.erase(remove(word.begin(), word.end(), 'i'), word.end());
	word.erase(remove(word.begin(), word.end(), 'c'), word.end());
}

string RemoveDuplicates(string word)
{
	string result = "";
	for (char c : word)
	{
		// result에 해당 문자가 아직 없으면 추가
		if (result.find(c) == string::npos)
		{
			result += c;
		}
	}
	return result;
}

vector<string> words;
vector<char> alphabet;

bool learned1[26] = { 0 };
int learnCnt = 0;

int maxLearn = 0;
int N, K;


// alphabet의 i번째 인덱스부터 에서 k개의 알파벳을 선택하여 학습
void Learning(int idx)
{
	int canRead = 0;

	if (learnCnt + (alphabet.size() - idx) < K)
	{
		return;
	}

	if (learnCnt == K)
	{
		// word 를 learned에 있는 알파벳으로 읽을 수 있는지 확인
		for (const string& word : words)
		{
			bool can = true;

			for (char c : word)
			{
				// learend 안에 c 가 없으면 읽을 수 없음
				if (!learned1[c - 'a'])
				{
					can = false;
					break;
				}
			}

			if (can)
			{
				canRead++;
			}
		}

		maxLearn = max(maxLearn, canRead);

		return;
	}

	for (int i = idx; i <= alphabet.size() - (K - learnCnt); i++)
	{
		//learned += alphabet[i];

		learned1[alphabet[i] - 'a'] = true;
		learnCnt++;

		Learning(i + 1);

		learned1[alphabet[i] - 'a'] = false;
		learnCnt--;
	}
}

int main()
{
	ios::sync_with_stdio(false);
	cin.tie(NULL);
	cout.tie(NULL);

	unordered_set<char> alpha;

	cin >> N >> K;

	int cnt = 0;

	for (int i = 0; i < N; i++)
	{
		string temp;
		cin >> temp;

		RemoveANTIC(temp);

		if (temp.length() == 0)
		{
			cnt++;
			continue;
		}

		for (char c : temp)
		{
			alpha.insert(c);
		}

		temp = RemoveDuplicates(temp);

		words.emplace_back(temp);
	}

	if (K < 5)
	{
		cout << 0;
		return 0;
	}

	if (K == 5)
	{
		cout << cnt;
		return 0;
	}

	if (K == 26)
	{
		cout << N;
		return 0;
	}


	alphabet.assign(alpha.begin(), alpha.end());

	K -= 5;

	if (K >= alphabet.size())
	{
		cout << N;
		return 0;
	}

	Learning(0);

	cout << maxLearn + cnt;
}