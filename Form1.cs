
using System;
using System.Drawing;
using System.Windows.Forms;

namespace SA_WorldGUI
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
            this.Paint += Form1_Paint;
        }

        private void Form1_Paint(object sender, PaintEventArgs e)
        {
            Graphics g = e.Graphics;

            using (Pen kalem = new Pen(Color.Blue, 3))
            {
                g.DrawArc(kalem, 50, 50, 200, 200, -45, 180);
            }
        }
    }
}
