#!/bin/python3

# Author : Alberto M. Esmoris Pena
# Script to plot performance data from logs
# See : logs_to_plots.sh


# ---  IMPORTS  --- #
# ----------------- #
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys
import os


# ---  CONFIGURATION CONSTANTS  --- #
# --------------------------------- #
markOptimumTime = False  # If True, plots will mark optimum time point

# ---  PREPARE OUTPUT DIRECTORY  --- #
# ---------------------------------- #
if len(sys.argv) < 2:
    print(
        '\nPlot from logs data cannot be generated.\n'
        'It is necessary to specify 2 input arguments:\n'
        '\t1: Path to input data CSV\n'
        '\t2: Path to output directory where plots will be exported\n'
    )
    sys.exit(2)
if not os.path.isdir(sys.argv[2]):
    if os.path.exists(sys.argv[2]):
        print(
            '"{path}" exists but it is not a directory'
            .format(path=sys.argv[2])
        )
        sys.exit(2)
    else:
        os.mkdir(sys.argv[2], 0o755)
outdir = '{path}{sep}'.format(path=sys.argv[2], sep=os.path.sep)


# ---  LOAD DATA  --- #
# ------------------- #
BASE_GROUP_LIST = [
    'KDTreeType', 'SAHNodes',
    'ParallelizationStrategy', 'ChunkSize', 'WarehouseFactor'
]
DF = pd.read_csv(sys.argv[1], header=0)
GDF = DF.groupby([
    'KDTreeType', 'SAHNodes',
    'ParallelizationStrategy', 'ChunkSize', 'WarehouseFactor',
    'SimulationCores', 'KDTBuildingCores'
]).mean()
GDF = DF.groupby(BASE_GROUP_LIST, as_index=True)
DFS = [GDF.get_group(g) for g in GDF.groups]


# ---  PLOT n SUMMARY --- #
# ----------------------- #
def key_from_index(index):
    kdtNum = index[0]
    if kdtNum == 1:
        return "KDT_SIMPLE"
    elif kdtNum == 2:
        return "KDT_SAH"
    elif kdtNum == 3:
        return "KDT_AXIS_SAH"
    elif kdtNum == 4:
        return "KDT_FAST_SAH"
    else:
        return "KDT_UNKNOWN"


def type_from_index(index):
    parallelNum = index[2]
    chunkSize = index[3]
    if parallelNum == 0:
        if chunkSize < 0:
            return "DYNAMIC"
        return "STATIC"
    elif parallelNum == 1:
        return "WAREHOUSE"
    else:
        return "UNKNOWN"


def title_from_index(index):
    # Extract subindices
    kdtNum = index[0]
    sahNodes = index[1]
    parallelNum = index[2]
    chunkSize = index[3]
    whFactor = index[4]

    # Text from subindices
    kdtType = 'UNKNOWN'
    parallelType = 'UNKNOWN'
    if kdtNum == 1:
        kdtType = 'Simple'
    elif kdtNum == 2:
        kdtType = 'SAH'
    elif kdtNum == 3:
        kdtType = 'AxisSAH'
    elif kdtNum == 4:
        kdtType = 'FastSAH'
    if parallelNum == 0:
        parallelType = 'Static scheduling with chunk size {chunkSize}'\
            .format(chunkSize=chunkSize)
        if chunkSize < 0:
            parallelType = 'Dynamic scheduling with chunk size {chunkSize}'\
                .format(chunkSize=chunkSize)
    elif parallelNum == 1:
        parallelType = 'Warehouse x{whFactor} with chunk size {chunkSize}'\
            .format(whFactor=whFactor, chunkSize=chunkSize)

    # Return title
    return \
        'Helios with {kdtType} KDTree of {sahNodes} nodes\n'\
        '{parallelType} parallelization'\
        .format(
            kdtType=kdtType,
            sahNodes=sahNodes,
            parallelType=parallelType
        )


def name_from_index(index):
    # Extract subindices
    kdtNum = index[0]
    sahNodes = index[1]
    parallelNum = index[2]
    chunkSize = index[3]
    whFactor = index[4]
    return 'KDT{kdt}_SAH{sah}_PS{ps}_CS_{cs}_WF{wf}'\
        .format(
            kdt=kdtNum,
            sah=sahNodes,
            ps=parallelNum,
            cs=chunkSize,
            wf=whFactor
        )


# Function to handle summary of performance measurements
def handle_summary(
    summary, summaryKey, summaryType,
    chunkSize, warehouseFactor, cores,
    kdtTime, simTime, fullTime,
    kdtSpeedup, simSpeedup, fullSpeedup
):
    minTimeArg = np.argmin(fullTime)
    minTime = fullTime[minTimeArg]
    sk = summary.get(summaryKey, None)
    # If summary key does not exist in summary
    if sk is None:
        summary[summaryKey] = {
            summaryType: {
                'chunkSize': chunkSize,
                'warehouseFactor': warehouseFactor,
                'cores': cores[minTimeArg],
                'kdtTime': kdtTime[minTimeArg],
                'simTime': simTime[minTimeArg],
                'fullTime': fullTime[minTimeArg],
                'kdtSpeedup': kdtSpeedup[minTimeArg],
                'simSpeedup': simSpeedup[minTimeArg],
                'fullSpeedup': fullSpeedup[minTimeArg]
            }
        }
    else:
        skt = sk.get(summaryType, None)
        # If summary key does exist in summary but summary type does not
        # Or if given summary key-type has a smaller full computation time
        if skt is None or skt['fullTime'] > minTime:
            sk[summaryType] = {
                'chunkSize': chunkSize,
                'warehouseFactor': warehouseFactor,
                'cores': cores[minTimeArg],
                'kdtTime': kdtTime[minTimeArg],
                'simTime': simTime[minTimeArg],
                'fullTime': fullTime[minTimeArg],
                'kdtSpeedup': kdtSpeedup[minTimeArg],
                'simSpeedup': simSpeedup[minTimeArg],
                'fullSpeedup': fullSpeedup[minTimeArg]
            }


# Function to print summary after it has been built
def print_summary(summary):
    print('\n\n\t\tSUMMARY\n\t=======================\n\n')
    for skey in summary.keys():
        print('{skey}:'.format(skey=skey))
        sk = summary[skey]
        for stype in sk.keys():
            print('\t{stype}:'.format(stype=stype))
            skt = sk[stype]
            print(
                '\t\tchunkSize: {chunkSize}\n'
                '\t\twarehouseFactor: {warehouseFactor}\n'
                '\t\tcores: {cores}\n'
                '\t\tkdtTime: {kdtTime}\n'
                '\t\tsimTime: {simTime}\n'
                '\t\tfullTime: {fullTime}\n'
                '\t\tkdtSpeedup: {kdtSpeedup}\n'
                '\t\tsimSpeedup: {simSpeedup}\n'
                '\t\tfullSpeedup: {fullSpeedup}\n'
                '\n'
                .format(
                    chunkSize=skt['chunkSize'],
                    warehouseFactor=skt['warehouseFactor'],
                    cores=skt['cores'],
                    kdtTime=skt['kdtTime'],
                    simTime=skt['simTime'],
                    fullTime=skt['fullTime'],
                    kdtSpeedup=skt['kdtSpeedup'],
                    simSpeedup=skt['simSpeedup'],
                    fullSpeedup=skt['fullSpeedup']
                )
            )


# Function to configure plots
def configure_plot(
    ax, xlabel='Cores', ylabel='Seconds',
    axx=None, yxlabel='Speed-up'
):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.autoscale(enable=True, axis='both', tight=True)
    ax.grid('both')
    ax.set_axisbelow(True)
    ax.legend(loc='center left')
    if axx is not None:
        axx.legend(loc='center right')
        axx.set_ylabel(yxlabel)
        axx.autoscale(enable=True, axis='both', tight=True)


summary = {}
for DF in DFS:
    # Extract data for the plot
    KDT = DF.drop('SimulationCores', axis=1).groupby(
        BASE_GROUP_LIST+['KDTBuildingCores']
    ).mean()
    SIM = DF.drop('KDTBuildingCores', axis=1).groupby(
        BASE_GROUP_LIST+['SimulationCores']
    ).mean()

    kdtCores = [x[5] for x in KDT.index]
    kdtTime = [x for x in KDT['KDTBuildTime']]
    kdtTime1 = KDT['KDTBuildTime'].iloc[0]
    kdtSpeedup = [kdtTime1/x for x in KDT['KDTBuildTime']]
    kdtTimeOptIdx = np.argmin(kdtTime)
    simCores = [x[5] for x in SIM.index]
    simTime = [x for x in SIM['SimulationTime']]
    simTime1 = SIM['SimulationTime'].iloc[0]
    simSpeedup = [simTime1/x for x in SIM['SimulationTime']]
    simTimeOptIdx = np.argmin(simTime)
    fullTime = np.add(kdtTime, simTime)
    fullTime1 = fullTime[0]
    fullSpeedup = [fullTime1/x for x in fullTime]
    fullTimeOptIdx = np.argmin(fullTime)

    # Fill summary
    summaryKey = key_from_index(KDT.index[0])
    summaryType = type_from_index(KDT.index[0])
    handle_summary(
        summary, summaryKey, summaryType,
        KDT.index[0][3], KDT.index[0][4], simCores,
        kdtTime, simTime, fullTime,
        kdtSpeedup, simSpeedup, fullSpeedup
    )

    # Debug section BEGIN ---
    # print('DF:\n', DF)
    # print('\nKDT:\n', KDT)
    # print('\nSIM:\n', SIM)
    # --- Debug section END

    # Prepare plot
    fig = plt.figure(figsize=(16, 9))
    plt.suptitle(title_from_index(KDT.index[0]))

    # Subplot 1
    ax = plt.subplot(2, 2, 1)
    ax.plot(
        kdtCores,
        kdtTime,
        lw=2,
        ls='-',
        color='blue',
        label='KDT building time'
    )
    if markOptimumTime:
        ax.scatter(
            kdtCores[kdtTimeOptIdx],
            kdtTime[kdtTimeOptIdx],
            s=64,
            c='blue',
            marker='o',
            edgecolors='black',
            zorder=4
        )
    axx = ax.twinx()
    axx.plot(
        kdtCores,
        kdtCores,
        color='black',
        lw=1,
        ls='--',
        label='Ideal speed-up'
    )
    axx.plot(
        kdtCores,
        kdtSpeedup,
        lw=1,
        ls='-',
        color='black',
        label='KDT building speed-up'
    )
    configure_plot(ax, xlabel='KDT Building cores', axx=axx)

    # Subplot 2
    ax = plt.subplot(2, 2, 2)
    ax.plot(
        simCores,
        simTime,
        lw=2,
        ls='-',
        color='green',
        label='Simulation time'
    )
    if markOptimumTime:
        ax.scatter(
            simCores[simTimeOptIdx],
            simTime[simTimeOptIdx],
            s=64,
            c='green',
            marker='o',
            edgecolors='black',
            zorder=4
        )
    axx = ax.twinx()
    axx.plot(
        simCores,
        simCores,
        color='black',
        lw=1,
        ls='--',
        label='Ideal speed-up'
    )
    axx.plot(
        simCores,
        simSpeedup,
        color='black',
        lw=1,
        ls='-',
        label='Simulation speed-up'
    )
    configure_plot(ax, xlabel='Simulation cores', axx=axx)

    # Subplot 3
    ax = plt.subplot(2, 2, 3)
    ax.plot(
        simCores,
        fullTime,
        lw=2,
        ls='-',
        color='red',
        label='Total time'
    )
    if markOptimumTime:
        ax.scatter(
            simCores[fullTimeOptIdx],
            fullTime[fullTimeOptIdx],
            s=64,
            c='red',
            marker='o',
            edgecolors='black',
            zorder=4
        )
    axx = ax.twinx()
    axx.plot(
        simCores,
        simCores,
        color='black',
        lw=1,
        ls='--',
        label='Ideal speed-up'
    )
    axx.plot(
        simCores,
        fullSpeedup,
        color='black',
        lw=1,
        ls='-',
        label='Simulation speed-up'
    )
    configure_plot(ax, axx=axx)

    # Subplot 4
    ax = plt.subplot(2, 2, 4)
    ax.plot(
        kdtCores,
        kdtTime,
        lw=2,
        ls='--',
        color='blue',
        label='KDT building time'
    )
    ax.plot(
        simCores,
        simTime,
        lw=2,
        ls='--',
        color='green',
        label='Simulation time'
    )
    ax.plot(
        simCores,
        fullTime,
        lw=2,
        ls='-',
        color='red',
        label='Total time'
    )
    if markOptimumTime:
        ax.scatter(
            simCores[fullTimeOptIdx],
            fullTime[fullTimeOptIdx],
            s=64,
            c='red',
            marker='o',
            edgecolors='black',
            zorder=4
        )
    axx = ax.twinx()
    axx.plot(
        simCores,
        simCores,
        color='black',
        lw=1,
        ls='--',
        label='Ideal speed-up'
    )
    axx.plot(
        simCores,
        fullSpeedup,
        color='black',
        lw=1,
        ls='-',
        label='Simulation speed-up'
    )
    configure_plot(ax, axx=axx)

    # Post-process plot
    plt.tight_layout()

    # Export plot
    # plt.show()
    plt.savefig(
        fname='{outpath}'.format(outpath='{outdir}{plotname}'
                                 .format(
                                    outdir=outdir,
                                    plotname=name_from_index(KDT.index[0])
                                 ))
    )
    plt.close()
    plt.cla()
    plt.clf()

print_summary(summary)
