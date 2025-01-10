#include <stdio.h>

extern struct rtpkt {
  int sourceid;       /* id of sending router sending this pkt */
  int destid;         /* id of router to which pkt being sent (must be an immediate neighbor) */
  int mincost[4];     /* min cost to node 0 ... 3 */
};

extern int TRACE;
extern int YES;
extern int NO;

struct distance_table 
{
  int costs[4][4];
} dt1;

static int connectcost[4] = {1, 0, 1, -1};
/* students to write the following two routines, and maybe some others */

void rtinit1() 
{
  for (int i = 0; i < 4; i++) dt1.costs[i][1] = connectcost[i];
  for (int i = 0; i < 4; i++) {
    if (i == 1) continue;
    for (int j = 0; j < 4; j++)
      dt1.costs[j][i] = -1;
  }
  struct rtpkt packet;
  packet.sourceid = 1;
  for (int i = 0; i < 4; i++)
    packet.mincost[i] = connectcost[i];
  for (int i = 0; i < 4; i++) {
    if (connectcost[i] == -1 || i == 1) continue;
    packet.destid = i;
    tolayer2(packet);
  }
}


void rtupdate1(rcvdpkt)
  struct rtpkt *rcvdpkt;
{
  int modify = 0;
  for (int i = 0; i < 4; i ++) {
    if (i == 1 || rcvdpkt->mincost[i] == -1) continue;
    int j = rcvdpkt->sourceid;
    if (dt1.costs[j][1] + rcvdpkt->mincost[i] < dt1.costs[i][j] || dt1.costs[i][j] == -1) {
      dt1.costs[i][j] = dt1.costs[j][1] + rcvdpkt->mincost[i];
      if (dt1.costs[i][j] < connectcost[i] || connectcost[i] == -1) {
        connectcost[i] = dt1.costs[i][j]; modify = 1;
      }
    }
  }
  if (modify) {
    struct rtpkt packet;
    packet.sourceid = 1;
    for (int i = 0; i < 4; i++) packet.mincost[i] = connectcost[i];
    for (int i = 0; i < 4; i++) {
      if (dt1.costs[i][1] == -1 || i == 1) continue;
      packet.destid = i; tolayer2(packet);
    }
  }
  printdt1(&dt1);
}


void printdt1(dtptr)
  struct distance_table *dtptr;
  
{
  printf("             via   \n");
  printf("   D1 |    0     2 \n");
  printf("  ----|-----------\n");
  printf("     0|  %3d   %3d\n",dtptr->costs[0][0], dtptr->costs[0][2]);
  printf("dest 2|  %3d   %3d\n",dtptr->costs[2][0], dtptr->costs[2][2]);
  printf("     3|  %3d   %3d\n",dtptr->costs[3][0], dtptr->costs[3][2]);

}



void linkhandler1(linkid, newcost)   
int linkid, newcost;   
/* called when cost from 1 to linkid changes from current value to newcost*/
/* You can leave this routine empty if you're an undergrad. If you want */
/* to use this routine, you'll need to change the value of the LINKCHANGE */
/* constant definition in prog3.c from 0 to 1 */
{
}

