import sys
#sys.path.append("../pyort/pyort/")
import argparse
from .pyort_fun import *

def main():    
    parser = argparse.ArgumentParser()
    parser.add_argument('-s','--start',action='store_true', help="Start monitoring of foregin IP's")
    parser.add_argument('-k','--kind',type=str,help="Similar to [kind] parameter in psutil.net_connections")
    parser.add_argument('-x','--silent',action='store_true',help="Silent mode, will not print any output")
    args = parser.parse_args()
    sys.stdout.write(str(pyort_start(args)))
    
def pyort_start(args):
       
    if args.start==True:
        configfile_name = "config.ini"
        directory=os.path.expanduser("~")+"/.config/pyort/" 
        
        #fetch values from config file
        db_path,db_name,time_interval,kd,hp_key,threat_update=config_para(directory,configfile_name)
        if args.kind != None: #kind argument from command line
            kd=args.kind
        print("\nMonitoring "+kd+" connections\n") 
        db_conn=sqlite_conn(db_path,db_name)
        while True:
            count=0
            conn=psutil.net_connections(kind=kd)
            for c in conn:
                fd= c[0]
                family_code=c[1]
                type_code=c[2]
                local_ip=extract_ip(c[3])
                local_port=extract_ip(c[3],False)
                remote_ip=extract_ip(c[4])
                remote_port=extract_ip(c[4],False)
                status_code=c[5]
                p_id=c[6]
                #if not an ip or a private ip then escape the loop
                if remote_ip==None or ipaddress.ip_address(unicode(remote_ip)).is_private==True:
                    continue
                                        
                #verfiy if the ip exists in the database
                is_record_exists, t_count,t_score=record_exists(db_conn,remote_ip)
        
                #updating project_honey_pot threat_score
                if hp_key!='' and int(count)%int(threat_update)==0:
                    threat_score,last_active=project_honey_pot(remote_ip,hp_key)
                else:
                    threat_score,last_active=None,None
                    
                if is_record_exists==False:                    
                    sql_query="""INSERT INTO pyort(fd,family,
                                       conn_type,local_ip,local_port,remote_ip,remote_port,
                                       status,pid,today_count,threat_score,last_active)
                                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"""

                    db_conn.execute(sql_query,(fd, family_code, type_code,str(local_ip),str(local_port),\
                                               str(remote_ip),str(remote_port),status_code,str(p_id),\
                                                count,str(threat_score),str(last_active)))
                else:            
                    sql_query="""UPDATE pyort SET last_time=DATETIME('now'),
                         today_count=today_count+1,threat_score=?,last_active=? where remote_ip=?"""
                    db_conn.execute(sql_query,(str(threat_score),str(last_active),remote_ip))
                if args.silent!=True:
                    print("Local= {:<15}:{:<6} Foreign= {:<15}:{:<6} PID= {:<6} Threat= {:<4} Count= {:<7} "\
                    .format(str(local_ip),str(local_port),str(remote_ip),str(remote_port),str(p_id),\
                    str(t_score),str(t_count)))


            db_conn.commit()

            time.sleep(float(time_interval))

        

if __name__=='__main__':     
    main()
