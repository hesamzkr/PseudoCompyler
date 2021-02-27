using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;

class Program
{
    public static void Main(string[] args)
    {
        bool isValid;
        isValid = validatePassword("a password");
    }
    public static bool validatePassword(string pass)
    {
        int LC, UP, Nums;
        char ch;
        LC = 0;
        UP = 0;
        Nums = 0;
        for (int i = 1; i < 10; i++)
        {
            ch = pass[i];
            if (ch >= '0' && ch <= '9')
            {
                Nums = Nums + 1;
            }
            else if (ch >= 'A' && ch <= 'Z')
            {
                UP = UP + 1;
            }
            else if (ch >= 'a' && ch <= 'z')
            {
                LC = LC + 1;
            }
            else
            {
                return false;
            }
        }
        if (LC >= 2 && UP >= 2 && Nums >= 3)
        {
            return true;
        }
        else
        {
            return false;
        }
    }

}