
from gnuradio import gr
import pmt

class blk(gr.basic_block):
    """Convert Zigbee Link Quality Indicator (LQI) (0..255) 
       to RFtap signal quality field (qual) (0.0..1.0)"""

    def __init__(self):
        gr.basic_block.__init__(
            self,
            name='LQI to qual',   # will show up in GRC
            in_sig=[],
            out_sig=[]
        )
        self.message_port_register_in(pmt.intern('in'))
        self.set_msg_handler(pmt.intern('in'), self.handle_msg)
        self.message_port_register_out(pmt.intern('out'))

    def handle_msg(self, pdu):
        meta, data = pmt.to_python(pdu)
        meta['qual'] = meta['lqi'] / 255.0
        pduout = pmt.cons(pmt.to_pmt(meta), pmt.to_pmt(data))
        self.message_port_pub(pmt.intern('out'), pduout)

