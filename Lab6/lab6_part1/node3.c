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
} dt3;

static int connectcost[4] = {7, -1, 2, 0};
/* students to write the following two routines, and maybe some others */

void rtinit3() 
{
  for (int i = 0; i < 4; i++) dt3.costs[i][3] = connectcost[i];
  for (int i = 0; i < 4; i++) {
    if (i == 3) continue;
    for (int j = 0; j < 4; j++)
      dt3.costs[j][i] = -1;
  }
  struct rtpkt packet;
  packet.sourceid = 3;
  for (int i = 0; i < 4; i++)
    packet.mincost[i] = connectcost[i];
  for (int i = 0; i < 4; i++) {
    if (connectcost[i] == -1 || i == 3) continue;
    packet.destid = i;
    tolayer2(packet);
  }
}


void rtupdate3(rcvdpkt)
  struct rtpkt *rcvdpkt;
{
  int modify = 0;
  for (int i = 0; i < 4; i++) {
    if (i == 3 || rcvdpkt->mincost[i] == -1) continue;
    int j = rcvdpkt->sourceid;
    if (dt3.costs[j][3] + rcvdpkt->mincost[i] < dt3.costs[i][j] || dt3.costs[i][j] == -1) {
      dt3.costs[i][j] = dt3.costs[j][3] + rcvdpkt->mincost[i];
      if (dt3.costs[i][j] < connectcost[i] || connectcost[i] == -1) {
        connectcost[i] = dt3.costs[i][j]; modify = 1;
      }
    }
  }
  if (modify) {
    struct rtpkt packet;
    packet.sourceid = 3;
    for (int i = 0; i < 4; i++) packet.mincost[i] = connectcost[i];
    for (int i = 0; i < 4; i++) {
      if (dt3.costs[i][3] == -1 || i == 3) continue;
      packet.destid = i; tolayer2(packet);
    }
  }
  printdt3(&dt3);
}


void printdt3(dtptr)
  struct distance_table *dtptr;
{
  printf("             via     \n");
  printf("   D3 |    0     2 \n");
  printf("  ----|-----------\n");
  printf("     0|  %3d   %3d\n",dtptr->costs[0][0], dtptr->costs[0][2]);
  printf("dest 1|  %3d   %3d\n",dtptr->costs[1][0], dtptr->costs[1][2]);
  printf("     2|  %3d   %3d\n",dtptr->costs[2][0], dtptr->costs[2][2]);
}






