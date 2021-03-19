FROM ubuntu:18.04

# Create Tektronix.rules as described in RSA API installation notes
RUN mkdir -p /etc/udev/rules.d/
RUN touch /etc/udev/rules.d/Tektronix.rules
RUN echo "SUBSYSTEM==\"usb\", ATTR{idVendor}==\"0699\", MODE=\"0666\", GROUP=\"plugdev\", ATTR{power/autosuspend =\"-1\", ATTR{power/control}=\"on\", ATTR{bMaxPower}=\"500mA\"" >> /etc/udev/rules.d/Tektronix.rules
RUN chmod a+r /etc/udev/rules.d/Tektronix.rules

# Create JSON mapping file for drivers
RUN touch /drivers/mapping.json
RUN echo "{\"scos_files\":[{\"source_path\":\"cyusb.conf\",\"dest_path\":\"/etc/cyusb.conf\"}]}" >> /drivers/mapping.json