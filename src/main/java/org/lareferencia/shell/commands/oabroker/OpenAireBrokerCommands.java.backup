
/*
 *   Copyright (c) 2013-2022. LA Referencia / Red CLARA and others
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU Affero General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU Affero General Public License for more details.
 *
 *   You should have received a copy of the GNU Affero General Public License
 *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 *   This file is part of LA Referencia software platform LRHarvester v4.x
 *   For any further information please contact Lautaro Matas <lmatas@gmail.com>
 */
package org.lareferencia.shell.commands.oabroker;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.lareferencia.core.oabroker.BrokerEvent;
import org.lareferencia.core.oabroker.BrokerEventRepository;
import org.lareferencia.core.util.SimpleJWSClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.shell.standard.ShellComponent;
import org.springframework.shell.standard.ShellMethod;

@ShellComponent
public class OpenAireBrokerCommands {
	
	private static Logger logger = LogManager.getLogger(OpenAireBrokerCommands.class);
	
	@Autowired
	BrokerEventRepository eventRepository;
	
	@ShellMethod("Query OpenAIRE API for broker events (experimental)")
	public String download_broker_events(long networkId, String opendoarId) throws Exception {
		
		eventRepository.deleteByNetworkID(networkId);
		
		SimpleJWSClient client = new SimpleJWSClient();
		
		JSONArray subscriptionResponse = (JSONArray) client.get("https://beta.api-broker.openaire.eu/subscriptions?email=" + opendoarId + "%40lareferencia.info");
		
		//subcriptionResponse.get(0).
		
		String subscriptionId = (String)((JSONObject)subscriptionResponse.get(0)).get("subscriptionId") ;
		
		JSONObject eventPage = (JSONObject) client.get("https://beta.api-broker.openaire.eu/scroll/notifications/bySubscriptionId/" + subscriptionId);
		Boolean completed = (Boolean) eventPage.get("completed");
		
		while ( !completed ) {
			
			JSONArray events = (JSONArray) eventPage.get("values");
			
			for ( Object eventObj: events.toArray() ) {

				JSONObject event = (JSONObject) eventObj;
				
				String id = (String) event.get("originalId") ;
				String msg = ( ((JSONObject) event.get("message")).toJSONString() );
				String topic = (String) event.get("topic") ;
				
				BrokerEvent e = new BrokerEvent(id, msg, topic, networkId); 
				
				eventRepository.save(e);
				
			}
			

			completed = (Boolean) eventPage.get("completed");
			
			if ( !completed ) {
				String scrollId = eventPage.get("id").toString();
				System.out.println("Scroll: " + scrollId);
				eventPage = (JSONObject) client.get("https://beta.api-broker.openaire.eu/scroll/notifications/" + scrollId);
			}
			
		}
		
		
		
		
			
		return "OK";
	}
	
	
}
