import com.google.gson.*;
import dev.robocode.tankroyale.common.recording.GameRecorder;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;

/** Native controller/observer wire adapter, deliberately does NOT launch bot processes. */
public final class Judge {
    static final Set<String> RECORD=Set.of("GameStartedEventForObserver","RoundStartedEvent",
        "TickEventForObserver","RoundEndedEventForObserver","GameEndedEventForObserver","GameAbortedEvent");
    static JsonObject setup(){
        JsonObject s=new JsonObject();s.addProperty("gameType","classic");
        s.addProperty("arenaWidth",800);s.addProperty("arenaHeight",600);s.addProperty("minNumberOfParticipants",2);
        s.addProperty("numberOfRounds",3);s.addProperty("gunCoolingRate",0.1);s.addProperty("maxInactivityTurns",450);
        s.addProperty("turnTimeout",150000);s.addProperty("readyTimeout",10000000);s.addProperty("defaultTurnsPerSecond",30);
        for(String k:List.of("ArenaWidth","ArenaHeight","MinNumberOfParticipants","MaxNumberOfParticipants","NumberOfRounds","GunCoolingRate","MaxInactivityTurns"))s.addProperty("is"+k+"Locked",true);
        s.addProperty("isTurnTimeoutLocked",false);s.addProperty("isReadyTimeoutLocked",false);return s;
    }
    static JsonObject botHandshakeCheck(JsonObject msg)throws IOException {
        if(!Wire.type(msg).equals("ServerHandshake") || !Wire.str(msg,"version").equals("1.4.0"))throw new IOException("SERVER_VERSION");
        return msg;
    }
    static JsonArray addresses(JsonObject list)throws IOException {
        if(!Wire.type(list).equals("BotListUpdate"))return null;
        JsonArray bots=list.getAsJsonArray("bots");if(bots.size()!=2)return null;
        Map<String,JsonObject> named=new HashMap<>();for(JsonElement e:bots){JsonObject b=e.getAsJsonObject();
            if(!Set.of("Walls","Spin Bot").contains(Wire.str(b,"name"))||!Wire.str(b,"version").equals("1.0"))throw new IOException("BOT_IDENTITIES");
            named.put(Wire.str(b,"name"),b);
        }
        if(named.size()!=2)throw new IOException("DUPLICATE_BOT");JsonArray a=new JsonArray();
        for(String name:List.of("Walls","Spin Bot")){JsonObject b=named.get(name),o=new JsonObject();
            o.add("host",b.get("host"));o.add("port",b.get("port"));a.add(o);}
        return a;
    }
    static void battle()throws Exception {
        Path out=Path.of("/tmp/evidence");Files.createDirectories(out.resolve("recordings"));
        Instant start=Instant.now();int ticks=0;List<Integer> rounds=new ArrayList<>();GameRecorder recorder=null;
        JsonObject finalEvent=null;String admin=Wire.env("ADMIN_SECRET");
        try(var observer=new Wire.Client("ws://127.0.0.1:7654");var controller=new Wire.Client("ws://127.0.0.1:7654")) {
            observer.handshake("ObserverHandshake",admin);controller.handshake("ControllerHandshake",admin);
            JsonObject c=Wire.parse(controller.take(5000),65536);
            if(!Wire.type(c).equals("BotListUpdate"))throw new IOException("ADMIN_ACK");
            JsonArray bots=null;long until=System.nanoTime()+TimeUnit.SECONDS.toNanos(40);
            while(bots==null && System.nanoTime()<until)bots=addresses(Wire.parse(observer.take(5000),65536));
            if(bots==null)throw new IOException("BOTS_NOT_CONNECTED");
            JsonObject command=Wire.obj("StartGame");command.add("gameSetup",setup());command.add("botAddresses",bots);controller.send(command);
            while(Duration.between(start,Instant.now()).toSeconds()<180) {
                String raw=observer.take(15000);JsonObject event=Wire.parse(raw,2*1024*1024);String type=Wire.type(event);
                if(type.equals("GameStartedEventForObserver")) {if(recorder!=null)throw new IOException("DUPLICATE_START");recorder=new GameRecorder(out.resolve("recordings").toString());}
                if(RECORD.contains(type)){if(recorder==null)throw new IOException("MISSING_GAME_START");recorder.record(raw);}
                if(type.equals("TickEventForObserver"))ticks++;
                if(type.equals("RoundEndedEventForObserver"))rounds.add(event.get("roundNumber").getAsInt());
                if(type.equals("GameAbortedEvent"))throw new IOException("ABORTED");
                if(type.equals("GameEndedEventForObserver")){finalEvent=event;break;}
            }
        } finally {if(recorder!=null)recorder.close();}
        if(finalEvent==null || !rounds.equals(List.of(1,2,3)) || ticks<1)throw new IOException("INCOMPLETE_BATTLE");
        JsonObject result=new JsonObject();result.addProperty("schema_version",1);result.addProperty("engine_version","1.4.0");
        result.addProperty("source","GameEndedEventForObserver");result.addProperty("completed",true);
        result.add("numberOfRounds",finalEvent.get("numberOfRounds"));result.add("results",finalEvent.get("results"));
        result.addProperty("observedTicks",ticks);JsonArray rr=new JsonArray();rounds.forEach(rr::add);result.add("observedRoundEnds",rr);
        result.addProperty("duration_ms",Duration.between(start,Instant.now()).toMillis());result.add("gameSetup",setup());
        Files.writeString(out.resolve("results.json"),result.toString(),StandardOpenOption.CREATE_NEW);
        try(var files=Files.walk(out)){for(Path p:files.filter(Files::isRegularFile).sorted().toList()){
            String name=out.relativize(p).toString().replace('\\','/');byte[] bytes=Files.readAllBytes(p);
            if(bytes.length>4*1024*1024)throw new IOException("ARTIFACT_LIMIT");
            System.out.println("ROBOCOPA_ARTIFACT "+name+" "+Base64.getEncoder().encodeToString(bytes));
        }}
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=1)throw new IllegalArgumentException("MODE");
        if(args[0].equals("server")) {
            Process p=new ProcessBuilder("java","-Xmx256m","-jar","/opt/i2/server.jar","--port=7654",
                "--tps=-1","--no-debug-mode","--no-breakpoint-mode","--controller-secrets="+Wire.env("ADMIN_SECRET"),
                "--bot-secrets="+Wire.env("BACKEND_SECRET"))
                .redirectErrorStream(true).redirectOutput(new File("/tmp/server.log")).start();
            Runtime.getRuntime().addShutdownHook(new Thread(p::destroyForcibly));
            int code=p.waitFor();if(code!=0)throw new IOException("ENGINE_EXIT");
        } else if(args[0].equals("battle"))battle();else throw new IllegalArgumentException("MODE");
    }
}
