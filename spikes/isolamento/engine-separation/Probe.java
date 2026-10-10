import com.google.gson.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;

/** Only bounded synthetic checks against this invocation's own endpoints. */
public final class Probe {
    static boolean connect(String host,int port){try(Socket s=new Socket()){s.connect(new InetSocketAddress(host,port),700);return true;}catch(IOException e){return false;}}
    static Map<String,String> officialEnvironment(String url,String frontSecret) {
        // The official 1.4.0 API expects SERVER_*, not our harness BOT_* names.
        return Map.of("SERVER_URL",url,"SERVER_SECRET",frontSecret);
    }
    static JsonObject botHello(JsonObject server){JsonObject h=Wire.obj("BotHandshake");h.add("sessionId",server.get("sessionId"));
        h.addProperty("name",Wire.env("BOT_NAME"));h.addProperty("version","1.0");h.addProperty("secret",Wire.env("BOT_SECRET"));
        JsonArray a=new JsonArray();a.add("fixture");h.add("authors",a);return h;}
    static void denied(String scenario)throws Exception {
        try(var c=new Wire.Client(Wire.env("BOT_SERVER_URL"))) {
            JsonObject s=Wire.parse(c.take(5000),65536);
            if(!Wire.type(s).equals("ServerHandshake"))throw new IOException("NO_POSITIVE_HANDSHAKE");
            JsonObject h=botHello(s);
            switch(scenario){
                case "controller_role": h.addProperty("type","ControllerHandshake");c.send(h);break;
                case "observer_role": h.addProperty("type","ObserverHandshake");c.send(h);break;
                case "before_auth_control": c.send(Wire.obj("PauseGame"));break;
                case "after_auth_control": c.send(h);Thread.sleep(80);c.send(Wire.obj("PauseGame"));break;
                case "second_handshake": c.send(h);Thread.sleep(80);c.send(h);break;
                case "wrong_identity": h.addProperty("name","NotThisParticipant");c.send(h);break;
                case "wrong_secret": h.addProperty("secret","invalid-fixture");c.send(h);break;
                case "duplicate_json": c.send("{\"type\":\"BotReady\",\"type\":\"PauseGame\"}");break;
                case "message_limit": c.send("{\"type\":\"BotHandshake\",\"padding\":\""+"x".repeat(18000)+"\"}");break;
                default: throw new IOException("UNKNOWN_CASE");
            }
            int code=c.awaitClose();if(code!=1008 && code!=1009)throw new IOException("EXPECTED_POLICY_CLOSE");
            JsonObject result=new JsonObject();result.addProperty("case",scenario);result.addProperty("denied",true);
            result.addProperty("close_code",code);System.out.println(result);
        }
    }
    static void network(String[] args)throws Exception {
        JsonObject checks=new JsonObject();String gateway=Wire.env("BOT_SERVER_URL");
        try(var c=new Wire.Client(gateway)){checks.addProperty("game_channel_alive",Wire.type(Wire.parse(c.take(5000),65536)).equals("ServerHandshake"));}
        checks.addProperty("own_canary_alive",connect("127.0.0.1",43123));
        checks.addProperty("peer_canary_denied",!connect(args[1],43123));
        checks.addProperty("judge_direct_denied",!connect(args[2],7654));
        checks.addProperty("runner_canary_denied",!connect(args[3],Integer.parseInt(args[4])));
        checks.addProperty("documentation_address_denied",!connect("192.0.2.1",9));
        checks.addProperty("gateway_backend_port_denied",!connect(URI.create(gateway).getHost(),7654));
        boolean defaultRoute=Files.readAllLines(Path.of("/proc/net/route")).stream().skip(1)
            .map(s->s.trim().split("\\s+")).anyMatch(p->p.length>1&&p[1].equals("00000000"));
        checks.addProperty("no_default_route",!defaultRoute);
        checks.addProperty("ipv6_disabled",Files.readString(Path.of("/proc/sys/net/ipv6/conf/all/disable_ipv6")).trim().equals("1"));
        checks.addProperty("no_admin_env",System.getenv("ADMIN_SECRET")==null && System.getenv("BACKEND_SECRET")==null);
        checks.addProperty("no_socket",!Files.exists(Path.of("/var/run/docker.sock")));
        for(var e:checks.entrySet())if(!e.getValue().getAsBoolean())throw new IOException("NETWORK_CHECK:"+e.getKey());
        System.out.println(checks);
    }
    static void waitBot()throws Exception {
        ServerSocket canary=new ServerSocket(43123);Thread t=new Thread(()->{while(!canary.isClosed())try(Socket s=canary.accept()){s.getOutputStream().write(42);}catch(IOException ignored){}});
        t.setDaemon(true);t.start();Files.writeString(Path.of("/tmp/bot-idle"),"ready");
        long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(180);
        while(!Files.exists(Path.of("/tmp/start-bot"))){if(System.nanoTime()>end)throw new IOException("BOT_START_TIMEOUT");Thread.sleep(100);}
        canary.close();t.join(1000);String name=Wire.env("BOT_NAME");
        String cls=name.equals("Walls")?"Walls":name.equals("Spin Bot")?"SpinBot":null;
        if(cls==null)throw new IOException("FIXED_BOT_REQUIRED");
        ProcessBuilder builder=new ProcessBuilder("java","-Xmx128m","-cp","/opt/i2/api.jar:/opt/i2/bots/"+cls,cls)
            .directory(new File("/opt/i2/bots/"+cls)).inheritIO();
        builder.environment().putAll(officialEnvironment(Wire.env("BOT_SERVER_URL"),Wire.env("BOT_SECRET")));
        builder.environment().remove("BOT_SERVER_URL");builder.environment().remove("BOT_SECRET");
        Process p=builder.start();Runtime.getRuntime().addShutdownHook(new Thread(p::destroyForcibly));
        if(p.waitFor()!=0)throw new IOException("BOT_PROCESS_EXIT");
    }
    public static void main(String[] args)throws Exception{
        switch(args[0]){
            case "namespaces": {
                JsonObject o=new JsonObject();o.addProperty("pid",Files.readSymbolicLink(Path.of("/proc/self/ns/pid")).toString());
                o.addProperty("mount",Files.readSymbolicLink(Path.of("/proc/self/ns/mnt")).toString());
                o.addProperty("network",Files.readSymbolicLink(Path.of("/proc/self/ns/net")).toString());
                System.out.println(o);break;
            }
            case "network":network(args);break;
            case "deny":denied(args[1]);break;
            case "idle":waitBot();break;
            case "start":Files.writeString(Path.of("/tmp/start-bot"),"start");break;
            case "read": if(!Set.of("/tmp/gate-report.json","/tmp/bot-idle","/tmp/gateway-ready").contains(args[1]))throw new IOException("PATH_DENIED");System.out.println(Files.readString(Path.of(args[1])));break;
            case "ready":if(!connect("127.0.0.1",7654))throw new IOException("SERVER_NOT_READY");break;
            default:throw new IOException("MODE_DENIED");
        }
    }
}
