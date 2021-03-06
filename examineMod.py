#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  1 12:54:02 2021

@author: akh
"""
import numpy as np 
import pandas as pd 
from fitRectangle import *
from htMOD import HT_center
from plotmod import HThist, plotlines
from sklearn.neighbors import NearestNeighbors

import matplotlib.pyplot as plt 

def clustered_lines(xs, ys, theta):
    xstart=max(xs)
    ystart=max(ys)
    
    xend=min(xs)
    yend=min(ys)
    
    xmid=(xstart+xend)/2
    ymid=(ystart+yend)/2
    l=np.sqrt( (xstart-xend)**2 + (ystart-yend)**2)
    a = np.cos(np.deg2rad(theta))
    b = np.sin(np.deg2rad(theta))
    
    x0 = xmid
    y0 = ymid
    x1 = int(x0 + l/2 * (-b))
    y1 = int(y0 + l/2 * (a))
    x2 = int(x0 - l/2 * (-b))
    y2 = int(y0 - l/2 * (a))
    
    return x1, x2, y1, y2

def checkoutCluster(dikeset, label):
    fig, ax=plt.subplots() 
    mask=(dikeset['Labels']==label)
    lines=dikeset[mask]
    plotlines(lines, 'r', ax)
    xc,yc=HT_center(dikeset)
    x,y=endpoints2(lines)
    plotlines(lines, 'r', ax, linewidth=3)
    #pltRec(lines, xc, yc, ax)
    #pltLine(lines, xc, yc, ax)
    
    return fig,ax

    
def examineClusters(clusters):
    
    #fig,ax=plt.subplots(1,3)
    clabel=np.unique(clusters['Labels'])
    nclusters=len(clabel)-1
    notclustered=sum([clusters['Labels']==-1][0])
    xc,yc=HT_center(clusters)
    clusters_data=pd.DataFrame()
    
    #print("Found", nclusters)
    #print( sum( clusters > -1), "clustered out of", len(p))
    sizes=[]
    
    cmask=np.full(len(clusters),False)
    for i in np.unique(clusters['Labels']): 
        clustered=True
        mask=clusters['Labels']==i
        lines=clusters[mask]
        cmask[mask]=True
        if (i == -1 or len(lines)<2):
            clustered=False
            
        x,y=endpoints2(lines)

        x0=(max(x)-min(x))/2
        y0=(max(y)-min(y))/2
        size=sum(mask)
        rrange=max(lines['rho'])-min(lines['rho'])
        trange=max(lines['theta'])-min(lines['theta'])
        avgrho=np.average(lines['rho'])
        avgtheta=np.average(lines['theta'])
        stdrho=np.std(lines['rho'])
        stdt=np.std(lines['theta'])
        segmentL=lines['seg_length'].sum()
        
        
        w,l=fit_Rec(lines, xc, yc)
        r=squaresError(lines,xc,yc)
        if r> 1000000: 
            continue 
        x1, x2, y1, y2=clustered_lines(x,y,avgtheta)
        #points=(np.vstack((x, y)).T)
        #sx,sy, ang=ellipse(points)
        Xe,Ye=RecEdges(lines, xc, yc)
        hashlines=pd.util.hash_pandas_object(lines['ID']).sum()
        
        clusters_data=clusters_data.append({ "Label": i, "Xstart": x1, "Ystart":y1, "Xend": x2, "Yend":y2, "X0": x0, "Y0": y0, "AvgRho":avgrho, "AvgTheta":avgtheta, "RhoRange":rrange,
         "ThetaRange": trange, "StdRho": stdrho, "StdTheta": stdt, "R_Width": w, "R_Length": l, "Size":size, "R_error":np.sqrt(r), "Linked":clustered, "SegmentLSum":segmentL, "Hash":hashlines}, ignore_index=True)
    
    #Find KNN distance of the endpoints 
    # Check that the KNN is not just one endpoint
    # Add to lines output
    X,Y=endpoints2(clusters_data)
    #X=clusters_data['Xstart'].values
    #Y=clusters_data['Ystart'].values
    X=(np.vstack((X, Y)).T)
    nbrs = NearestNeighbors(n_neighbors=3, algorithm='ball_tree').fit(X)
    distances, indices = nbrs.kneighbors(X)
    s=0
    distAvg=[]
    for i in range(int(len(indices)/2)): 
        if distances[i,1]==clusters_data['R_Length'].iloc[i]:
            s=s+1
            print("matched to endpoint", s)
            distAvg.append(min(distances[i,2],distances[i*2,2]))
            continue
            
        distAvg.append(min(distances[i,1],distances[i*2,1]))
        
        

    
    
    clusters_data["KNN2"]=distAvg
    

    X=clusters_data['Xstart'].values
    Y=clusters_data['Ystart'].values
    X=(np.vstack((X, Y)).T)
    nbrs = NearestNeighbors(n_neighbors=3, algorithm='ball_tree').fit(X)
    distances, indices = nbrs.kneighbors(X)
    s=0
    distAvg=[]
    for i in range(int(len(indices))): 
        if distances[i,1]==clusters_data['R_Length'].iloc[i]:
            s=s+1
            print("matched to endpoint", s)
            distAvg.append(distances[i,2])
            continue
            
        distAvg.append(distances[i,1])
        
    clusters_data["KNN"]=distAvg

    
    
    evaluation=pd.DataFrame({ "Ic": (len(clusters)-notclustered),
                              "nClusters": nclusters,
                              "AverageRhoRange": np.average(clusters_data["RhoRange"]),                              
                              "AverageThetaRange": np.average(clusters_data["ThetaRange"]),
                              "StdRhoRange": np.std(clusters_data["RhoRange"]),
                              "StdThetaRange": np.std(clusters_data["ThetaRange"]),
                              "AvgClusterSize": np.average(clusters_data["Size"]),
                              "ClusterSizeStd": np.std(clusters_data["Size"]),
                              "ClusterMax": clusters_data["Size"].max(), 
                              "AverageL": np.average(clusters_data["R_Length"]),
                              "AverageW": np.average(clusters_data["R_Width"])},                           
                              index=[0])
    
    #print(evaluation)
    #plt.tight_layout()
    return clusters_data, evaluation

def ClusteredAll(dikeset,lines,cmask):
    notClustered=dikeset.iloc[~cmask]

def errorAnalysis(lines):
    
    fig,ax=plt.subplots(2,4)
    ax[0][0].set_ylabel('R_length')
    ax[0][0].scatter(lines['R_error'], lines['R_Length'])
    ax[0][1].scatter(lines['R_error'], lines['R_Width'])
    ax[0][1].set_ylabel('R_Width')
    
    ax[0][2].scatter(lines['R_error'], lines['Size'])
    ax[0][2].set_ylabel('Size')
    
    
    ax[0][3].hist(lines['R_error'], bins=50)
    ax[0][3].set_ylabel('Counts')
    
    ax[1][0].scatter(lines['R_error'], lines['AvgTheta'])
    ax[1][0].set_ylabel('AvgTheta')
    
    ax[1][1].scatter(lines['R_error'], lines['AvgRho'])
    ax[1][1].set_ylabel('AvgRho')
    
    ax[1][2].scatter(lines['R_error'], lines['ThetaRange'])
    ax[1][2].set_ylabel('ThetaRange')
    
    ax[1][3].scatter(lines['R_error'], lines['RhoRange'])
    ax[1][3].set_ylabel('RhoRange')
    
    for i in range(4):
        ax[1][i].set_xlabel("SS Error (m)")
    print("Error evaluation")
    print("average error:", lines['R_error'].mean())
    print("# clusters over 1 mil error:", max(lines['Label'])-len(lines))
    print("N% clustered", (np.sum(lines['Size'])/4262)*100)
        
def TopHTSection(lines, rstep, tstep):
    fig,ax=plt.subplots(1,2)
    
    ax[0],img=HThist(lines['AvgRho'], lines['AvgTheta'], rstep=rstep, tstep=tstep, ax=ax[0])
    h=img[0]
    
    xedges=img[1]
    yedges=img[2]
    
    [i,j]=np.unravel_index(h.argmax(), h.shape)
    
    
    xe=[xedges[i],xedges[i+1]]
    ye=[yedges[j],yedges[j+1]]
    print(h.max(), "clustered lines at", xe, "degrees", ye, "rho (m)" )
    #     masklat= (dikeset['latitude'] > lat1) & (dikeset['latitude'] < lat2)
    # masklong=(dikeset['longitude'] > lon1) & (dikeset['longitude'] < lon2)
    # masklatlong= (masklat==1) & (masklong==1)
    
    maskTheta=(lines['AvgTheta'] > xe[0]) & (lines['AvgTheta'] < xe[1])
    maskRho=(lines['AvgRho'] > ye[0]) & (lines['AvgRho'] < ye[1])
    mask=(maskTheta ==True) & (maskRho==True)

    print(np.sum(mask), "should equal", h.max())
    print(np.sum(mask)==h.max())
    toplines=lines[mask]
    plotlines(lines, 'k', ax[1], alpha=0.1)
    plotlines(toplines, 'r', ax[1])
    print(toplines['Size'].sum(), "dike segements")
    
    return toplines

def plotlabel(df,label):
    fig,ax=plt.subplots()
    mask=df['Labels']==label
    xc,yc=HT_center(df)
    lines=df[mask]
    plotlines(lines,"r", ax)
    x,y=endpoints2(lines)
    w,l=fit_Rec(lines, xc, yc)
    r=squaresError(lines,xc,yc)
    avgtheta=np.average(lines['theta'])

    x1, x2, y1, y2=clustered_lines(x,y,avgtheta)
    ax.plot([x1,x2], [y1,y2], 'g')
    
    ax.set_title("Label"+str(label))
    ax.text( .89, .89, "W:"+str(w),transform=ax.transAxes )
    ax.text( .84, .84, "L:"+str(l),transform=ax.transAxes  )
    ax.text( .80, .80, "errors:"+str(r),transform=ax.transAxes  )
         
    
