using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;

class Program
{
    public static void Main(string[] args)
    {
        Console.WriteLine($"{validatePassword("MyPass")}");
    }
    public static bool validatePassword(string pass)
    {
        if (pass == "MyPass")
        {
            return false;
        }
        else if (pass == "MyPass?")
        {
            return false;
        }
        else
        {
            return true;
        }
    }

}