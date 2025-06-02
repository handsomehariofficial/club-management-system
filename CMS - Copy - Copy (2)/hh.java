import java.util.Arrays;
class largest{
    int[] lgest(int aa[])
    {
        Arrays.sort(aa);
        return aa;
    }
    public static void main(String args[])
    {
        int[] aa = {1,3,2,4,1};
        largest l = new largest();
        int[] s = l.lgest(aa);
        for(int i = 0;i<s.length;i++)
        {
            System.out.print(s[i]);
        }
        System.out.println();
        System.out.println("Smallest element : "+s[0]);
        System.out.println("largest element : "+s[(s.length)-1]);
        for(int i =0;i<s.length-2;i++)
        {
            if(s[i]!=s[i+1])
            {
            System.out.println("second largest =" +s[i+1]);

break;        }
            
            if(s[s.length-2]!=s[s.length-1])
            {
                System.out.println("second smallest "+s[s.length-2]);
            }
