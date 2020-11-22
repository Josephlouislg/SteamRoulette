debug:
	@read -p "Enter apps for scale 0  separated by space  " apps_array && \
	for a in $$apps_array; do \
		echo $$a ; \
		docker-compose scale $$a=0; \
	done;
	make restart_nginx;


restart_nginx:
	docker-compose restart nginx;