#include <stdio.h>

extern struct rtpkt {
  int sourceid;       /* id of sending router sending this pkt */
  int destid;         /* id of router to which pkt being sent (must be an immediate neighbor) */
  int mincost[4];     /* min cost to node 0 ... 3 */
};

extern int TRACE;
extern int YES;
extern int NO;
extern clocktime;

struct distance_table 
{
  int costs[4][4];
} dt0;

static int connectcost[4] = {0, 1, 3, 7};
/* students to write the following two routines, and maybe some others */

void rtinit0()
{
  for (int i = 0; i < 4; i++) dt0.costs[i][0] = connectcost[i];
  for (int i = 0; i < 4; i++) {
    if (i == 0) continue;
    for (int j = 0; j < 4; j++)
      dt0.costs[j][i] = -1;
  }
  struct rtpkt packet;
  packet.sourceid = 0;
  for (int i = 0; i < 4; i ++) 
    packet.mincost[i] = connectcost[i];
  for (int i = 1; i < 4; i ++) {
    if (dt0.costs[i][0] == -1) continue;
    packet.destid = i;
    tolayer2(packet);
  }
}


void rtupdate0(rcvdpkt)
  struct rtpkt *rcvdpkt;
{
  int modify = 0;
  for (int i = 0; i < 4; i ++) {
    if (i == 0 || rcvdpkt->mincost[i] == -1) continue;
    int j = rcvdpkt->sourceid;
    if (dt0.costs[j][0] + rcvdpkt->mincost[i] < dt0.costs[i][j] || dt0.costs[i][j] == -1) {
      dt0.costs[i][j] = dt0.costs[j][0] + rcvdpkt->mincost[i];
      if (dt0.costs[i][j] < connectcost[i] || connectcost[i] == -1) {
        connectcost[i] = dt0.costs[i][j]; modify = 1;
      }
    }
  }
  if (modify) {
    struct rtpkt packet;
    packet.sourceid = 0;
    for (int i = 0; i < 4; i ++) packet.mincost[i] = connectcost[i];
    for (int i = 0; i < 4; i ++) {
      if (dt0.costs[i][0] == -1 || i == 0) continue;
      packet.destid = i; tolayer2(packet);
    }
  }
  printdt0(&dt0);
}


void printdt0(dtptr)
  struct distance_table *dtptr;
  
{
  printf("                via     \n");
  printf("   D0 |    1     2    3 \n");
  printf("  ----|-----------------\n");
  printf("     1|  %3d   %3d   %3d\n",dtptr->costs[1][1],
   dtptr->costs[1][2],dtptr->costs[1][3]);
  printf("dest 2|  %3d   %3d   %3d\n",dtptr->costs[2][1],
   dtptr->costs[2][2],dtptr->costs[2][3]);
  printf("     3|  %3d   %3d   %3d\n",dtptr->costs[3][1],
   dtptr->costs[3][2],dtptr->costs[3][3]);
}


void linkhandler0(linkid, newcost)   
  int linkid, newcost;
/* called when cost from 0 to linkid changes from current value to newcost*/
/* You can leave this routine empty if you're an undergrad. If you want */
/* to use this routine, you'll need to change the value of the LINKCHANGE */
/* constant definition in prog3.c from 0 to 1 */
{
}
