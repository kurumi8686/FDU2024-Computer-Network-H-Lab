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
} dt2;

static int connectcost[4] = {3, 1, 0, 2};
/* students to write the following two routines, and maybe some others */

void rtinit2() 
{
  for (int i = 0; i < 4; i++) dt2.costs[i][2] = connectcost[i];
  for (int i = 0; i < 4; i++) {
    if (i == 2) continue;
    for (int j = 0; j < 4; j++)
      dt2.costs[j][i] = -1;
  }
  struct rtpkt packet;
  packet.sourceid = 2;
  for (int i = 0; i < 4; i++)
    packet.mincost[i] = connectcost[i];
  for (int i = 0; i < 4; i++) {
    if (connectcost[i] == -1 || i == 2) continue;
    packet.destid = i;
    tolayer2(packet);
  }
}


void rtupdate2(rcvdpkt)
  struct rtpkt *rcvdpkt;
{
  int modify = 0;
  for (int i = 0; i < 4; i++) {
    if (i == 2 || rcvdpkt->mincost[i] == -1) continue;
    int j = rcvdpkt->sourceid;
    if (dt2.costs[j][2] + rcvdpkt->mincost[i] < dt2.costs[i][j] || dt2.costs[i][j] == -1) {
      dt2.costs[i][j] = dt2.costs[j][2] + rcvdpkt->mincost[i];
      if (dt2.costs[i][j] < connectcost[i] || connectcost[i] == -1) {
        connectcost[i] = dt2.costs[i][j]; modify = 1;
      }
    }
  }
  if (modify) {
    struct rtpkt packet;
    packet.sourceid = 2;
    for (int i = 0; i < 4; i ++) packet.mincost[i] = connectcost[i];
    for (int i = 0; i < 4; i++) {
      if (dt2.costs[i][2] == -1 || i == 2) continue;
      packet.destid = i; tolayer2(packet);
    }
  }
  printdt2(&dt2);
}


void printdt2(dtptr)
  struct distance_table *dtptr;
  
{
  printf("                via     \n");
  printf("   D2 |    0     1    3 \n");
  printf("  ----|-----------------\n");
  printf("     0|  %3d   %3d   %3d\n",dtptr->costs[0][0],
   dtptr->costs[0][1],dtptr->costs[0][3]);
  printf("dest 1|  %3d   %3d   %3d\n",dtptr->costs[1][0],
   dtptr->costs[1][1],dtptr->costs[1][3]);
  printf("     3|  %3d   %3d   %3d\n",dtptr->costs[3][0],
   dtptr->costs[3][1],dtptr->costs[3][3]);
}


