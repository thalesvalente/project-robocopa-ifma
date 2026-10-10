/** Driver factory: no connection URL or role from an HTTP body. */
export function createDispatch(sql) {
  return async (digest,{requestId,operation,args})=>sql.begin(async tx=>{
    await tx`SET LOCAL statement_timeout = '3s'`;
    await tx`SET LOCAL lock_timeout = '1s'`;
    const rows=await tx`SELECT rc_control.worker_command(${digest},${requestId}::uuid,${operation},${tx.json(args)}::jsonb) AS response`;
    if(rows.length!==1)throw Error('RESPONSE_INVALID');
    return rows[0].response;
  });
}
